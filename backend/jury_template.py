from io import BytesIO
from pathlib import Path

import xlsxwriter

from criteria import CRITERIA, MAX_TOTAL, header

AUTHOR = "Офлайн-агрегатор оценок"
FIRST_ROW = 5  # первая строка с участниками (нумерация с нуля, это 6-я строка листа)
MIN_ROWS = 50


def build_template(participants=None, section=""):
    """Собирает шаблон для жюри и возвращает содержимое xlsx."""
    names = [name.strip() for name in (participants or []) if name.strip()]
    rows_count = max(MIN_ROWS, len(names))

    output = BytesIO()
    book = xlsxwriter.Workbook(output, {"in_memory": True})
    book.set_properties({"title": "Шаблон оценки жюри", "author": AUTHOR})

    title = book.add_format({"bold": True, "font_size": 14})
    label = book.add_format({"bold": True})
    field = book.add_format({"bg_color": "#FFF2CC", "border": 1})
    head = book.add_format({"bold": True, "text_wrap": True, "align": "center", "valign": "vcenter",
                            "bg_color": "#E4F0FF", "border": 1})
    num = book.add_format({"border": 1, "align": "center"})
    fio = book.add_format({"border": 1})
    score = book.add_format({"border": 1, "align": "center", "num_format": "0"})
    total = book.add_format({"border": 1, "align": "center", "bold": True})
    comment = book.add_format({"border": 1, "text_wrap": True, "valign": "top"})
    small = book.add_format({"font_size": 9, "italic": True, "font_color": "#555555"})

    sheet = book.add_worksheet("Бланк")
    sheet.merge_range("A1:P1", "Лист экспертной оценки работ и выступлений участников", title)
    sheet.write("A2", "Секция:", label)
    sheet.merge_range("B2:F2", section, field)
    sheet.write("A3", "ФИО эксперта:", label)
    sheet.merge_range("B3:F3", "", field)

    sheet.set_row(4, 60)
    sheet.write(4, 0, "№", head)
    sheet.write(4, 1, "ФИО участника", head)
    for i, (short, _, max_score, _) in enumerate(CRITERIA):
        sheet.write(4, 2 + i, header(short, max_score), head)
    total_col = 2 + len(CRITERIA)
    sheet.write(4, total_col, f"Итого (макс. {MAX_TOTAL})", head)
    sheet.write(4, total_col + 1, "Комментарий / совет на будущее", head)

    last_row = FIRST_ROW + rows_count - 1
    for n in range(rows_count):
        row = FIRST_ROW + n
        sheet.write(row, 0, n + 1, num)
        sheet.write(row, 1, names[n] if n < len(names) else "", fio)
        for i in range(len(CRITERIA)):
            sheet.write_blank(row, 2 + i, None, score)
        excel_row = row + 1
        sheet.write_formula(row, total_col, f'=IF(COUNT(C{excel_row}:N{excel_row})=0,"",SUM(C{excel_row}:N{excel_row}))',
                            total, "")
        sheet.write_blank(row, total_col + 1, None, comment)

    for i, (_, _, max_score, _) in enumerate(CRITERIA):
        sheet.data_validation(FIRST_ROW, 2 + i, last_row, 2 + i, {
            "validate": "integer",
            "criteria": "between",
            "minimum": 0,
            "maximum": max_score,
            "input_title": "Баллы",
            "input_message": f"Целое число от 0 до {max_score}",
            "error_title": "Неверный балл",
            "error_message": f"Можно ввести целое число от 0 до {max_score}",
        })

    sheet.write(last_row + 2, 0, "Баллы целые. Пустые строки не учитываются. "
                                 "Подробнее о критериях на листе «Справочник».", small)
    sheet.freeze_panes(5, 2)
    sheet.set_column("A:A", 5)
    sheet.set_column("B:B", 32)
    sheet.set_column("C:N", 13)
    sheet.set_column("O:O", 11)
    sheet.set_column("P:P", 45)
    sheet.set_landscape()
    sheet.set_paper(9)
    sheet.fit_to_pages(1, 0)

    ref = book.add_worksheet("Справочник")
    ref_head = book.add_format({"bold": True, "border": 1, "bg_color": "#E4F0FF", "valign": "vcenter"})
    ref_cell = book.add_format({"border": 1, "text_wrap": True, "valign": "top"})
    ref_center = book.add_format({"border": 1, "align": "center", "valign": "top"})
    ref_total = book.add_format({"border": 1, "bold": True})
    ref_total_center = book.add_format({"border": 1, "bold": True, "align": "center"})
    for col, text in enumerate(["№", "Критерий", "Баллы", "Показатель оценивания"]):
        ref.write(0, col, text, ref_head)
    for i, (_, full_name, max_score, indicator) in enumerate(CRITERIA):
        ref.write(1 + i, 0, i + 1, ref_center)
        ref.write(1 + i, 1, full_name, ref_cell)
        ref.write(1 + i, 2, f"от 0 до {max_score}", ref_center)
        ref.write(1 + i, 3, indicator, ref_cell)
    total_row = 1 + len(CRITERIA)
    ref.write(total_row, 0, "", ref_total)
    ref.write(total_row, 1, "Итого", ref_total)
    ref.write(total_row, 2, MAX_TOTAL, ref_total_center)
    ref.write(total_row, 3, "", ref_total)
    ref.set_column("A:A", 5)
    ref.set_column("B:B", 45)
    ref.set_column("C:C", 10)
    ref.set_column("D:D", 90)
    ref.freeze_panes(1, 0)

    book.close()
    return output.getvalue()


if __name__ == "__main__":
    target = Path(__file__).parent.parent / "docs" / "Шаблон_оценки_жюри.xlsx"
    target.write_bytes(build_template())
    print("Записан файл", target.name)
