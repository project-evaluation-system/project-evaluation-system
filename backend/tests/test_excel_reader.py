from io import BytesIO

import openpyxl

from excel_reader import read_expert_file


def test_valid_file_is_read(make_expert_file, good_scores):
    data = make_expert_file([("Иванов Иван", good_scores, "Хорошая работа")])
    sheet, errors = read_expert_file("e1.xlsx", data)
    assert errors == []
    assert sheet["file"] == "e1.xlsx"
    assert sheet["expert"] == "Соколова Н.А."
    assert sheet["section"] == "Робототехника"
    assert len(sheet["rows"]) == 1
    row = sheet["rows"][0]
    assert row["fio"] == "Иванов Иван"
    assert row["comment"] == "Хорошая работа"
    assert row["scores"]["Актуальность"] == 2
    assert row["scores"]["Отзыв партнёра"] == 1


def test_expert_name_from_file_name_if_header_is_empty(make_expert_file, good_scores):
    data = make_expert_file([("Иванов Иван", good_scores, "")], expert="", section="")
    sheet, errors = read_expert_file("Эксперт_2_Морозов.xlsx", data)
    assert errors == []
    assert sheet["expert"] == "Эксперт_2_Морозов"
    assert sheet["section"] == ""


def test_comma_decimal_is_accepted(make_expert_file, good_scores):
    scores = ["2,5"] + good_scores[1:]
    sheet, errors = read_expert_file("e.xlsx", make_expert_file([("Иванов Иван", scores, "")]))
    assert errors == []
    assert sheet["rows"][0]["scores"]["Актуальность"] == 2.5


def test_rows_without_fio_are_skipped(make_expert_file, good_scores):
    data = make_expert_file([("Иванов Иван", good_scores, ""), ("", good_scores, "")])
    sheet, errors = read_expert_file("e.xlsx", data)
    assert errors == []
    assert len(sheet["rows"]) == 1


def test_score_above_max_is_error(make_expert_file, good_scores):
    scores = [good_scores[0], 5] + good_scores[2:]
    sheet, errors = read_expert_file("e.xlsx", make_expert_file([("Белова Дарья", scores, "")]))
    assert sheet is None
    assert errors == ["В файле «e.xlsx» у участника «Белова Дарья» "
                      "балл по критерию «Логичность и полнота» = 5 (максимум 4)."]


def test_text_instead_of_number_is_error(make_expert_file, good_scores):
    scores = ["пять"] + good_scores[1:]
    _, errors = read_expert_file("e.xlsx", make_expert_file([("Жуков Лев", scores, "")]))
    assert errors == ["В файле «e.xlsx» у участника «Жуков Лев» "
                      "балл по критерию «Актуальность»: «пять», а нужно число."]


def test_empty_criterion_is_error(make_expert_file, good_scores):
    scores = good_scores[:5] + [None] + good_scores[6:]
    _, errors = read_expert_file("e.xlsx", make_expert_file([("Зайцева Алиса", scores, "")]))
    assert errors == ["В файле «e.xlsx» у участника «Зайцева Алиса» не заполнен критерий «Практические навыки»."]


def test_sum_above_max_total_is_error(make_expert_file):
    scores = [3, 4, 6, 5, 3, 5, 4, 4, 4, 3, 3, 9]
    _, errors = read_expert_file("e.xlsx", make_expert_file([("Перебор", scores, "")]))
    assert "В файле «e.xlsx» у участника «Перебор» сумма баллов = 53 (максимум 45)." in errors


def test_duplicate_participant_is_error(make_expert_file, good_scores):
    data = make_expert_file([("Иванов Иван", good_scores, ""), ("иванов  иван", good_scores, "")])
    _, errors = read_expert_file("e.xlsx", data)
    assert errors == ["В файле «e.xlsx» участник «иванов  иван» встречается несколько раз."]


def test_all_errors_of_file_are_collected(make_expert_file, good_scores):
    bad_range = [good_scores[0], 5] + good_scores[2:]
    bad_text = ["abc"] + good_scores[1:]
    data = make_expert_file([("Первый", bad_range, ""), ("Второй", bad_text, "")])
    _, errors = read_expert_file("e.xlsx", data)
    assert len(errors) == 2


def test_file_without_participants_is_error(make_expert_file):
    _, errors = read_expert_file("e.xlsx", make_expert_file([]))
    assert errors == ["В файле «e.xlsx» нет ни одного оценённого участника."]


def test_missing_header_is_error():
    book = openpyxl.Workbook()
    book.active.append(["что-то", "другое"])
    output = BytesIO()
    book.save(output)
    sheet, errors = read_expert_file("e.xlsx", output.getvalue())
    assert sheet is None
    assert "не найдена шапка таблицы" in errors[0]


def test_missing_criteria_columns_are_listed():
    book = openpyxl.Workbook()
    book.active.append(["ФИО участника", "Актуальность (0-3)"])
    output = BytesIO()
    book.save(output)
    _, errors = read_expert_file("e.xlsx", output.getvalue())
    assert errors[0].startswith("В файле «e.xlsx» нет столбцов: «Логичность и полнота», ")


def test_not_xlsx_is_error():
    sheet, errors = read_expert_file("scores.xls", b"abc")
    assert sheet is None
    assert errors == ["Файл «scores.xls» не в формате .xlsx. Сохраните его в Excel как «Книга Excel (.xlsx)»."]


def test_broken_file_is_error():
    _, errors = read_expert_file("e.xlsx", b"not an excel file")
    assert errors == ["Не удалось открыть файл «e.xlsx». Проверьте, что это заполненный шаблон для жюри."]


def test_file_over_5_mb_is_error():
    _, errors = read_expert_file("e.xlsx", b"x" * (5 * 1024 * 1024 + 1))
    assert errors == ["Файл «e.xlsx» больше 5 МБ."]
