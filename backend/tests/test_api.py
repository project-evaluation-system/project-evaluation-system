from io import BytesIO
from urllib.parse import unquote

import openpyxl
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

NAMES = ["Эксперт_1_Соколова.xlsx", "Эксперт_2_Морозов.xlsx", "Эксперт_3_Лебедева.xlsx"]


def three_files(make_expert_file, good_scores):
    weaker = [max(score - 1, 0) for score in good_scores]
    files = []
    for i, name in enumerate(NAMES):
        rows = [("Иванов Иван", good_scores, "Добавьте выводы" if i == 0 else ""), ("Петров Пётр", weaker, "")]
        files.append(("files", (name, make_expert_file(rows, expert=f"Эксперт {i + 1}"))))
    return files


def test_index_page_opens():
    response = client.get("/")
    assert response.status_code == 200
    assert "Офлайн-агрегатор оценок" in response.text


def test_one_file_is_rejected(make_expert_file, good_scores):
    response = client.post("/upload/", files=three_files(make_expert_file, good_scores)[:1])
    assert response.status_code == 400
    assert response.json()["errors"] == ["Нужно загрузить от 2 до 5 файлов, а загружено 1."]


def test_six_files_are_rejected(make_expert_file, good_scores):
    files = three_files(make_expert_file, good_scores) * 2
    response = client.post("/upload/", files=files)
    assert response.status_code == 400
    assert response.json()["errors"] == ["Нужно загрузить от 2 до 5 файлов, а загружено 6."]


def test_three_files_give_rating(make_expert_file, good_scores):
    response = client.post("/upload/", files=three_files(make_expert_file, good_scores))
    assert response.status_code == 200
    data = response.json()
    assert [(r["place"], r["fio"]) for r in data["results"]] == [(1, "Иванов Иван"), (2, "Петров Пётр")]
    assert data["results"][0]["total"] == sum(good_scores)
    assert data["results"][0]["experts_count"] == 3
    assert data["section"] == "Робототехника"
    assert len(data["experts"]) == 3
    assert data["advice"] == [{"fio": "Иванов Иван", "items": [{"expert": "Эксперт 1", "text": "Добавьте выводы"}]}]


def test_errors_are_returned_for_all_files(make_expert_file, good_scores):
    files = three_files(make_expert_file, good_scores)
    too_high = [good_scores[0], 5] + good_scores[2:]
    not_a_number = ["пять"] + good_scores[1:]
    files[0] = ("files", (NAMES[0], make_expert_file([("Белова Дарья", too_high, "")])))
    files[1] = ("files", (NAMES[1], make_expert_file([("Жуков Лев", not_a_number, "")])))
    response = client.post("/upload/", files=files)
    assert response.status_code == 400
    errors = response.json()["errors"]
    assert errors == [
        "В файле «Эксперт_1_Соколова.xlsx» у участника «Белова Дарья» "
        "балл по критерию «Логичность и полнота» = 5 (максимум 4).",
        "В файле «Эксперт_2_Морозов.xlsx» у участника «Жуков Лев» "
        "балл по критерию «Актуальность»: «пять», а нужно число.",
    ]


def test_not_xlsx_file_is_rejected(make_expert_file, good_scores):
    files = three_files(make_expert_file, good_scores)[:2]
    files.append(("files", ("оценки.xls", b"abc")))
    response = client.post("/upload/", files=files)
    assert response.status_code == 400
    assert "Файл «оценки.xls» не в формате .xlsx" in response.json()["errors"][0]


def test_report_has_three_sheets(make_expert_file, good_scores):
    response = client.post("/generate-report/", files=three_files(make_expert_file, good_scores))
    assert response.status_code == 200
    disposition = response.headers["content-disposition"]
    assert unquote(disposition.split("filename*=UTF-8''")[1]) == "Итоговый_рейтинг.xlsx"
    book = openpyxl.load_workbook(BytesIO(response.content))
    assert book.sheetnames == ["Рейтинг", "Советы на будущее", "Оценки экспертов"]
    assert book["Рейтинг"]["B6"].value == "Иванов Иван"
    assert book["Оценки экспертов"].max_row == 7


def test_report_with_errors_is_rejected(make_expert_file, good_scores):
    files = three_files(make_expert_file, good_scores)[:1]
    response = client.post("/generate-report/", files=files)
    assert response.status_code == 400


def test_empty_template_download():
    response = client.get("/download-template")
    assert response.status_code == 200
    assert "filename*=UTF-8''" in response.headers["content-disposition"]
    book = openpyxl.load_workbook(BytesIO(response.content))
    assert book.sheetnames == ["Бланк", "Справочник"]
    assert book["Бланк"]["B6"].value is None


def test_template_with_participants():
    response = client.post("/download-template", data={"participants": "Иванов Иван\nПетров Пётр\n", "section": "Химия"})
    assert response.status_code == 200
    sheet = openpyxl.load_workbook(BytesIO(response.content))["Бланк"]
    assert sheet["B2"].value == "Химия"
    assert [sheet["B6"].value, sheet["B7"].value, sheet["B8"].value] == ["Иванов Иван", "Петров Пётр", None]
