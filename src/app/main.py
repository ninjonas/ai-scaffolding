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
    from app.agents.tools.knowledge import make_read_knowledge_file_tool
    from app.infrastructure.repositories.knowledge_file import SQLKnowledgeFileRepository

    def knowledge_uow_factory() -> SQLAlchemyUnitOfWork:
        return SQLAlchemyUnitOfWork(session_factory)

    def make_knowledge_repo() -> SQLKnowledgeFileRepository:
        return SQLKnowledgeFileRepository(session_factory())

    read_knowledge_file = make_read_knowledge_file_tool(make_knowledge_repo)
    agent_graph = create_supervisor_graph(llm, extra_tools=[read_knowledge_file])
    orchestrator = AgentOrchestrator(agent_graph)
    broker = AgentBroker(orchestrator)
    uow = SQLAlchemyUnitOfWork(session_factory)
    knowledge_service = KnowledgeService(uow_factory=knowledge_uow_factory, llm=llm)
    chat_service = ChatService(
        broker=broker, unit_of_work=uow, knowledge_service=knowledge_service
    )

    _container = Container(settings=settings)
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
