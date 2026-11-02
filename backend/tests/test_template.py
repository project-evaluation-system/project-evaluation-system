from io import BytesIO

import openpyxl

from criteria import CRITERIA, MAX_TOTAL
from jury_template import build_template


def open_template(**kwargs):
    return openpyxl.load_workbook(BytesIO(build_template(**kwargs)))


def test_max_total_is_45():
    assert len(CRITERIA) == 12
    assert MAX_TOTAL == 45
    assert sum(max_score for _, _, max_score, _ in CRITERIA) == 45


def test_sheets_and_header():
    book = open_template()
    assert book.sheetnames == ["Бланк", "Справочник"]
    header = [cell.value for cell in book["Бланк"][5]]
    assert header[1] == "ФИО участника"
    assert header[2] == "Актуальность (0-3)"
    assert header[13] == "Отзыв партнёра (0-1)"
    assert len(header[2:14]) == 12


def test_every_criterion_has_validation_with_right_max():
    sheet = open_template()["Бланк"]
    rules = sheet.data_validations.dataValidation
    assert len(rules) == 12
    for i, (_, _, max_score, _) in enumerate(CRITERIA):
        letter = openpyxl.utils.get_column_letter(3 + i)
        rule = next(r for r in rules if str(r.sqref).startswith(letter + "6"))
        assert rule.type == "whole"
        assert (rule.formula1, rule.formula2) == ("0", str(max_score))


def test_participants_and_section_are_filled():
    sheet = open_template(participants=["Иванов Иван", "Петров Пётр"], section="Химия")["Бланк"]
    assert sheet["B2"].value == "Химия"
    assert sheet["B6"].value == "Иванов Иван"
    assert sheet["B7"].value == "Петров Пётр"
    assert sheet["B8"].value is None
    assert sheet["A55"].value == 50


def test_author():
    book = open_template()
    assert book.properties.creator == "Офлайн-агрегатор оценок"
