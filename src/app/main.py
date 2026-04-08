from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Scaffolding API")

WEB_DIST = Path(__file__).resolve().parent.parent / "web" / "dist"


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


if WEB_DIST.is_dir():
    app.mount("/assets", StaticFiles(directory=WEB_DIST / "assets"), name="assets")

    @app.get("/{path:path}")
    async def serve_spa(path: str) -> FileResponse:
        file = WEB_DIST / path
        if file.is_file():
            return FileResponse(file)
        return FileResponse(WEB_DIST / "index.html")
