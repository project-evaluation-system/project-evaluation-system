from io import BytesIO

import openpyxl
import pytest

from jury_template import build_template

# 34 балла из 45, все значения в пределах максимумов
GOOD_SCORES = [2, 3, 5, 4, 2, 4, 3, 3, 3, 2, 2, 1]


@pytest.fixture
def good_scores():
    return list(GOOD_SCORES)


@pytest.fixture
def make_expert_file():
    """Собирает файл эксперта по шаблону: rows = [(ФИО, 12 баллов, комментарий), ...]."""

    def make(rows, expert="Соколова Н.А.", section="Робототехника"):
        book = openpyxl.load_workbook(BytesIO(build_template()))
        sheet = book["Бланк"]
        sheet["B2"] = section
        sheet["B3"] = expert
        for i, (fio, scores, comment) in enumerate(rows):
            row = 6 + i
            sheet.cell(row, 2, fio)
            for j, score in enumerate(scores):
                sheet.cell(row, 3 + j, score)
            sheet.cell(row, 16, comment)
        output = BytesIO()
        book.save(output)
        return output.getvalue()

    return make
