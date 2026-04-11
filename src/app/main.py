from contextlib import asynccontextmanager
from pathlib import Path

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.agents.orchestrator import AgentBroker, AgentOrchestrator
from app.api.router import api_router
from app.infrastructure.database import create_engine, create_session_factory, init_database
from app.infrastructure.unit_of_work import SQLAlchemyUnitOfWork
from app.service.chat import ChatService
from app.service.knowledge import KnowledgeService
from app.shared.config import Settings
from app.shared.di import Container
from app.shared.llm import create_llm
from app.shared.logging import configure_logging

log = structlog.get_logger()

WEB_DIST = Path(__file__).resolve().parent.parent / "web" / "dist"

settings = Settings()
_container: Container | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _container

    configure_logging(log_level=settings.log_level, log_json=settings.log_json)
    log.info("app_starting", log_level=settings.log_level)

    engine = create_engine(settings.database_url)
    await init_database(engine)
    session_factory = create_session_factory(engine)

    llm = create_llm(settings)

    from app.agents.supervisor.graph import create_supervisor_graph
    from app.agents.tools.knowledge import make_search_knowledge_tool
    from app.agents.tools.memory import make_search_memory_tool
    from app.infrastructure.vector.client import get_chroma_client
    from app.infrastructure.vector.knowledge_indexer import KnowledgeIndexer
    from app.infrastructure.vector.knowledge_searcher import KnowledgeSearcher
    from app.infrastructure.vector.memory_searcher import MemorySearcher
    from app.infrastructure.vector.message_indexer import MessageIndexer

    def knowledge_uow_factory() -> SQLAlchemyUnitOfWork:
        return SQLAlchemyUnitOfWork(session_factory)

    import aiosqlite
    from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

    checkpoint_db_path = settings.checkpoint_db_path
    Path(checkpoint_db_path).parent.mkdir(parents=True, exist_ok=True)
    log.info("checkpointer_init", db_path=checkpoint_db_path)
    conn = await aiosqlite.connect(checkpoint_db_path)
    checkpointer = AsyncSqliteSaver(conn)
    log.info("checkpointer_ready", db_path=checkpoint_db_path)

    chroma_client = get_chroma_client(settings)
    knowledge_indexer = KnowledgeIndexer(chroma_client, settings)
    knowledge_searcher = KnowledgeSearcher(chroma_client, settings)
    memory_searcher = MemorySearcher(chroma_client, settings)
    message_indexer = MessageIndexer(chroma_client, settings)

    search_knowledge = make_search_knowledge_tool(knowledge_searcher)
    search_memory = make_search_memory_tool(memory_searcher)

    agent_graph = create_supervisor_graph(llm, extra_tools=[search_knowledge, search_memory], checkpointer=checkpointer)
    orchestrator = AgentOrchestrator(agent_graph)
    broker = AgentBroker(orchestrator)
    uow = SQLAlchemyUnitOfWork(session_factory)
    knowledge_service = KnowledgeService(uow_factory=knowledge_uow_factory, llm=llm, indexer=knowledge_indexer)
    chat_service = ChatService(
        broker=broker,
        unit_of_work=uow,
        knowledge_service=knowledge_service,
        message_indexer=message_indexer,
    )

    _container = Container(settings=settings)
    _container._register("checkpointer", checkpointer)
    _container._register("chat_service", chat_service)
    _container._register("knowledge_service", knowledge_service)

    import asyncio

    import app.shared.di as di_module

    di_module._container = _container

    async with knowledge_uow_factory() as uow:
        all_files = await uow.knowledge.list(scope=None, conversation_id=None)
        unenriched = [f for f in all_files if not f.enriched]

    backfill_tasks: set[asyncio.Task] = set()
    if unenriched:
        log.info("knowledge_backfill_start", count=len(unenriched))
        for f in unenriched:
            task = asyncio.create_task(knowledge_service.enrich_metadata(f.id))
            backfill_tasks.add(task)
            task.add_done_callback(backfill_tasks.discard)

    log.info("app_started")
    yield

    await engine.dispose()
    log.info("app_stopped")


app = FastAPI(title="Scaffolding API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

if WEB_DIST.is_dir():
    app.mount("/assets", StaticFiles(directory=WEB_DIST / "assets"), name="assets")

    @app.get("/{path:path}")
    async def serve_spa(path: str) -> FileResponse:
        file = WEB_DIST / path
        if file.is_file():
            return FileResponse(file)
        return FileResponse(WEB_DIST / "index.html")
