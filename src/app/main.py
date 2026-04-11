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

    agent_graph = create_supervisor_graph(llm)
    orchestrator = AgentOrchestrator(agent_graph)
    broker = AgentBroker(orchestrator)
    uow = SQLAlchemyUnitOfWork(session_factory)
    knowledge_service = KnowledgeService(session_factory=session_factory)
    chat_service = ChatService(
        broker=broker, unit_of_work=uow, knowledge_service=knowledge_service
    )

    _container = Container(settings=settings)
    _container._register("chat_service", chat_service)
    _container._register("knowledge_service", knowledge_service)

    import app.shared.di as di_module

    di_module._container = _container

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
