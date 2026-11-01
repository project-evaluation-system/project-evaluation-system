from datetime import datetime
from io import BytesIO

import xlsxwriter

from criteria import header

AUTHOR = "Офлайн-агрегатор оценок"


def write_rating_sheet(book, rating, formats):
    sheet = book.add_worksheet("Рейтинг")
    experts_count = len(rating["experts"])
    created = datetime.now().strftime("%d.%m.%Y %H:%M")

    sheet.write(0, 0, "Итоговый рейтинг", formats["title"])
    sheet.write(1, 0, f"Секция: {rating['section']}")
    sheet.write(2, 0, f"Сформирован: {created}, экспертов: {experts_count}")

    heads = ["Место", "ФИО участника", "Итоговый балл", "Экспертов"]
    heads += [header(c["short"], c["max"]) for c in rating["criteria"]]
    for col, text in enumerate(heads):
        sheet.write(4, col, text, formats["head"])

    for i, result in enumerate(rating["results"]):
        row = 5 + i
        sheet.write(row, 0, result["place"], formats["center"])
        sheet.write(row, 1, result["fio"], formats["cell"])
        sheet.write(row, 2, result["total"], formats["number_bold"])
        sheet.write(row, 3, result["experts_count"], formats["center"])
        for j, c in enumerate(rating["criteria"]):
            sheet.write(row, 4 + j, result["criteria"][c["short"]], formats["number"])

    last_row = 4 + max(len(rating["results"]), 1)
    sheet.autofilter(4, 0, last_row, len(heads) - 1)
    sheet.freeze_panes(5, 2)
    sheet.set_row(4, 60)
    sheet.set_column(0, 0, 8)
    sheet.set_column(1, 1, 32)
    sheet.set_column(2, 3, 13)
    sheet.set_column(4, len(heads) - 1, 14)


def write_advice_sheet(book, rating, formats):
    sheet = book.add_worksheet("Советы на будущее")
    for col, text in enumerate(["ФИО участника", "Эксперт", "Совет"]):
        sheet.write(0, col, text, formats["head"])

    row = 1
    for item in rating["advice"]:
        for i, advice in enumerate(item["items"]):
            sheet.write(row, 0, item["fio"] if i == 0 else "", formats["wrap"])
            sheet.write(row, 1, advice["expert"], formats["wrap"])
            sheet.write(row, 2, advice["text"], formats["wrap"])
            row += 1
    if row == 1:
        sheet.write(1, 0, "Комментариев нет", formats["wrap"])

    sheet.freeze_panes(1, 0)
    sheet.set_column(0, 0, 32)
    sheet.set_column(1, 1, 24)
    sheet.set_column(2, 2, 80)


def build_report(rating, sheets):
    """Итоговый отчёт в xlsx: рейтинг и советы (оценки экспертов добавим отдельным шагом)."""
    output = BytesIO()
    book = xlsxwriter.Workbook(output, {"in_memory": True})
    book.set_properties({"title": "Итоговый рейтинг", "author": AUTHOR})

    formats = {
        "title": book.add_format({"bold": True, "font_size": 14}),
        "head": book.add_format({"bold": True, "text_wrap": True, "align": "center", "valign": "vcenter",
                                 "bg_color": "#E4F0FF", "border": 1}),
        "cell": book.add_format({"border": 1}),
        "center": book.add_format({"border": 1, "align": "center"}),
        "number": book.add_format({"border": 1, "align": "center", "num_format": "0.00"}),
        "number_bold": book.add_format({"border": 1, "align": "center", "num_format": "0.00", "bold": True}),
        "wrap": book.add_format({"border": 1, "text_wrap": True, "valign": "top"}),
    }

    write_rating_sheet(book, rating, formats)
    write_advice_sheet(book, rating, formats)

    book.close()
    return output.getvalue()
