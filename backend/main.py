from pathlib import Path

from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

BASE_DIR = Path(__file__).parent

app = FastAPI(title="Офлайн-агрегатор оценок")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def read_root():
    return (BASE_DIR / "templates" / "index.html").read_text(encoding="utf-8")


@app.post("/upload/")
async def upload_files(files: list[UploadFile] = File(...)):
    # Заглушка: пока только возвращаем имена файлов
    return {"files": [f.filename for f in files]}
