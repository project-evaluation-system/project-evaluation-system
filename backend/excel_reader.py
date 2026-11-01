import math
from io import BytesIO
from pathlib import Path

import pandas as pd

from criteria import CRITERIA, normalize

MAX_SIZE = 5 * 1024 * 1024
HEADER_SEARCH_ROWS = 15


def cell_text(value):
    if pd.isna(value):
        return ""
    return normalize(value)


def to_number(value):
    """Число из ячейки; «2,5» тоже подходит; если не число, вернёт None."""
    try:
        number = float(str(value).strip().replace(",", "."))
    except ValueError:
        return None
    if not math.isfinite(number):
        return None
    return number


def find_header(table):
    """Ищет шапку: строка и столбец ячейки «ФИО участника»."""
    for row in range(min(HEADER_SEARCH_ROWS, len(table))):
        for col in range(table.shape[1]):
            if cell_text(table.iat[row, col]) == "фио участника":
                return row, col
    return None, None


def find_value_right(table, header_row, label):
    """Значение справа от подписи («ФИО эксперта:», «Секция:») в строках выше шапки."""
    for row in range(header_row):
        for col in range(table.shape[1]):
            if cell_text(table.iat[row, col]) != label:
                continue
            for value_col in range(col + 1, table.shape[1]):
                value = table.iat[row, value_col]
                if not pd.isna(value) and str(value).strip():
                    return str(value).strip()
    return ""


def read_rows(table, header_row, fio_col, columns, comment_col):
    rows = []
    for row in range(header_row + 1, len(table)):
        fio = table.iat[row, fio_col]
        if pd.isna(fio) or not str(fio).strip():
            continue
        scores = {}
        for short, col in columns.items():
            scores[short] = to_number(table.iat[row, col])
        comment = ""
        if comment_col is not None and not pd.isna(table.iat[row, comment_col]):
            comment = str(table.iat[row, comment_col]).strip()
        rows.append({"fio": str(fio).strip(), "scores": scores, "comment": comment})
    return rows


def read_expert_file(filename, content):
    """Читает файл одного эксперта. Возвращает (лист, ошибки): при ошибках листа нет."""
    if not filename.lower().endswith(".xlsx"):
        return None, [f"Файл «{filename}» не в формате .xlsx. Сохраните его в Excel как «Книга Excel (.xlsx)»."]
    if len(content) > MAX_SIZE:
        return None, [f"Файл «{filename}» больше 5 МБ."]

    try:
        sheets = pd.read_excel(BytesIO(content), sheet_name=None, header=None, engine="openpyxl")
    except Exception:
        return None, [f"Не удалось открыть файл «{filename}». Проверьте, что это заполненный шаблон для жюри."]

    table = sheets["Бланк"] if "Бланк" in sheets else next(iter(sheets.values()))

    header_row, fio_col = find_header(table)
    if header_row is None:
        return None, [f"В файле «{filename}» не найдена шапка таблицы (столбец «ФИО участника»). "
                      "Используйте шаблон для жюри."]

    header = {col: cell_text(table.iat[header_row, col]) for col in range(table.shape[1])}
    columns = {}
    for short, _, _, _ in CRITERIA:
        for col, text in header.items():
            if text.startswith(normalize(short)):
                columns[short] = col
                break
    missing = [short for short, _, _, _ in CRITERIA if short not in columns]
    if missing:
        names = "», «".join(missing)
        return None, [f"В файле «{filename}» нет столбцов: «{names}»."]

    comment_col = None
    for col, text in header.items():
        if text.startswith("комментарий"):
            comment_col = col
            break

    sheet = {
        "file": filename,
        "expert": find_value_right(table, header_row, "фио эксперта") or Path(filename).stem,
        "section": find_value_right(table, header_row, "секция"),
        "rows": read_rows(table, header_row, fio_col, columns, comment_col),
    }
    return sheet, []
