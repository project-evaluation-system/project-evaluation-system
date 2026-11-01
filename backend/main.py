from pathlib import Path
from urllib.parse import quote

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

from excel_reader import read_expert_file
from jury_template import build_template
from rating import calculate_rating
from report import build_report

BASE_DIR = Path(__file__).parent
XLSX_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
MIN_FILES = 2
MAX_FILES = 5

app = FastAPI(title="Офлайн-агрегатор оценок")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


def xlsx_response(content, filename):
    # кириллицу в заголовке можно передать только в filename*
    disposition = f"attachment; filename=\"report.xlsx\"; filename*=UTF-8''{quote(filename)}"
    return Response(content, media_type=XLSX_TYPE, headers={"Content-Disposition": disposition})


def errors_response(errors, sheets=()):
    warnings = []
    if len(sheets) >= MIN_FILES:
        warnings = calculate_rating(list(sheets))["warnings"]
    return JSONResponse({"errors": errors, "warnings": warnings}, status_code=400)


async def read_all(files):
    """Читает все загруженные файлы. Возвращает (листы, ошибки по всем файлам)."""
    if not MIN_FILES <= len(files) <= MAX_FILES:
        return [], [f"Нужно загрузить от {MIN_FILES} до {MAX_FILES} файлов, а загружено {len(files)}."]
    sheets = []
    errors = []
    for upload in files:
        sheet, file_errors = read_expert_file(upload.filename or "", await upload.read())
        if sheet:
            sheets.append(sheet)
        errors.extend(file_errors)
    return sheets, errors


@app.get("/", response_class=HTMLResponse)
async def read_root():
    return (BASE_DIR / "templates" / "index.html").read_text(encoding="utf-8")


@app.get("/download-template")
async def download_template():
    return xlsx_response(build_template(), "Шаблон_оценки_жюри.xlsx")


@app.post("/download-template")
async def download_template_with_participants(participants: str = Form(""), section: str = Form("")):
    content = build_template(participants.splitlines(), section.strip())
    return xlsx_response(content, "Шаблон_оценки_жюри.xlsx")


@app.post("/upload/")
async def upload_files(files: list[UploadFile] = File(default=[])):
    sheets, errors = await read_all(files)
    if errors:
        return errors_response(errors, sheets)
    return calculate_rating(sheets)


@app.post("/generate-report/")
async def generate_report(files: list[UploadFile] = File(default=[])):
    sheets, errors = await read_all(files)
    if errors:
        return errors_response(errors, sheets)
    return xlsx_response(build_report(calculate_rating(sheets), sheets), "Итоговый_рейтинг.xlsx")
