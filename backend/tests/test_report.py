from io import BytesIO

import openpyxl

from criteria import CRITERIA
from report import build_report


def make_sheet(file, expert, rows):
    return {
        "file": file,
        "expert": expert,
        "section": "Робототехника",
        "rows": [
            {"fio": fio, "scores": {short: score for short, _, _, _ in CRITERIA}, "comment": comment}
            for fio, score, comment in rows
        ],
    }


def make_rating(advice):
    criteria = [{"short": short, "max": max_score} for short, _, max_score, _ in CRITERIA]
    return {
        "section": "Робототехника",
        "experts": [{"name": "Соколова Н.А.", "file": "1.xlsx"}, {"name": "Морозов К.В.", "file": "2.xlsx"}],
        "criteria": criteria,
        "results": [
            {"place": 1, "fio": "Иванов Иван", "total": 30.5, "experts_count": 2,
             "criteria": {short: 2.5 for short, _, _, _ in CRITERIA}},
            {"place": 2, "fio": "Петров Пётр", "total": 24, "experts_count": 2,
             "criteria": {short: 2.0 for short, _, _, _ in CRITERIA}},
        ],
        "advice": advice,
        "warnings": [],
    }


def open_report(rating, sheets):
    return openpyxl.load_workbook(BytesIO(build_report(rating, sheets)))


SHEETS = [
    make_sheet("1.xlsx", "Соколова Н.А.", [("Иванов Иван", 3, "Добавьте выводы"), ("Петров Пётр", 2, "")]),
    make_sheet("2.xlsx", "Морозов К.В.", [("Иванов Иван", 2, ""), ("Петров Пётр", 2, "")]),
]
ADVICE = [{"fio": "Иванов Иван", "items": [{"expert": "Соколова Н.А.", "text": "Добавьте выводы"}]}]


def test_report_has_three_sheets():
    book = open_report(make_rating(ADVICE), SHEETS)
    assert book.sheetnames == ["Рейтинг", "Советы на будущее", "Оценки экспертов"]
    assert book.properties.creator == "Офлайн-агрегатор оценок"


def test_rating_sheet_numbers():
    sheet = open_report(make_rating(ADVICE), SHEETS)["Рейтинг"]
    assert sheet["A1"].value == "Итоговый рейтинг"
    assert sheet["A2"].value == "Секция: Робототехника"
    assert "экспертов: 2" in sheet["A3"].value
    assert [c.value for c in sheet[5]][:5] == ["Место", "ФИО участника", "Итоговый балл", "Экспертов", "Актуальность (0-3)"]
    assert [c.value for c in sheet[6]][:5] == [1, "Иванов Иван", 30.5, 2, 2.5]
    assert sheet["C6"].number_format == "0.00"
    assert sheet["B7"].value == "Петров Пётр"


def test_advice_sheet_and_empty_advice():
    sheet = open_report(make_rating(ADVICE), SHEETS)["Советы на будущее"]
    assert [c.value for c in sheet[2]] == ["Иванов Иван", "Соколова Н.А.", "Добавьте выводы"]
    empty = open_report(make_rating([]), SHEETS)["Советы на будущее"]
    assert empty["A2"].value == "Комментариев нет"


def test_scores_sheet_has_all_rows_and_sums():
    sheet = open_report(make_rating(ADVICE), SHEETS)["Оценки экспертов"]
    assert sheet.max_row == 5
    first = [c.value for c in sheet[2]]
    assert first[:3] == ["Соколова Н.А.", "1.xlsx", "Иванов Иван"]
    assert first[-1] == 36
    assert [c.value for c in sheet[5]][-1] == 24
