from criteria import CRITERIA
from rating import calculate_rating


def make_sheet(file, expert, rows, section="Робототехника"):
    """rows = [(ФИО, балл по каждому критерию, комментарий)]."""
    return {
        "file": file,
        "expert": expert,
        "section": section,
        "rows": [
            {"fio": fio, "scores": {short: score for short, _, _, _ in CRITERIA}, "comment": comment}
            for fio, score, comment in rows
        ],
    }


def test_average_by_criteria_and_total():
    first = make_sheet("1.xlsx", "Соколова Н.А.", [("Иванов Иван", 2, "")])
    second = make_sheet("2.xlsx", "Морозов К.В.", [("Иванов Иван", 1, "")])
    rating = calculate_rating([first, second])
    result = rating["results"][0]
    assert result["criteria"]["Актуальность"] == 1.5
    assert result["total"] == 18
    assert result["experts_count"] == 2


def test_results_are_sorted_by_total_then_name():
    sheet = make_sheet("1.xlsx", "Соколова Н.А.", [("Яковлев", 1, ""), ("Белов", 3, ""), ("Алексеев", 1, "")])
    other = make_sheet("2.xlsx", "Морозов К.В.", [("Яковлев", 1, ""), ("Белов", 3, ""), ("Алексеев", 1, "")])
    names = [r["fio"] for r in calculate_rating([sheet, other])["results"]]
    assert names == ["Белов", "Алексеев", "Яковлев"]


def test_equal_totals_share_a_place():
    sheet = make_sheet("1.xlsx", "Соколова Н.А.",
                       [("Первый", 3, ""), ("Второй", 2, ""), ("Третий", 2, ""), ("Четвёртый", 1, "")])
    places = [r["place"] for r in calculate_rating([sheet, sheet])["results"]]
    assert places == [1, 2, 2, 4]


def test_same_participant_is_matched_by_normalized_name():
    first = make_sheet("1.xlsx", "Соколова Н.А.", [("Артём Денисов", 2, "")])
    second = make_sheet("2.xlsx", "Морозов К.В.", [("артем  денисов", 2, "")])
    results = calculate_rating([first, second])["results"]
    assert len(results) == 1
    assert results[0]["fio"] == "Артём Денисов"


def test_participant_missing_in_some_files_gives_warning():
    first = make_sheet("1.xlsx", "Соколова Н.А.", [("Иванов Иван", 2, ""), ("Петров Пётр", 2, "")])
    second = make_sheet("2.xlsx", "Морозов К.В.", [("Иванов Иван", 2, "")])
    third = make_sheet("3.xlsx", "Лебедева О.И.", [("Иванов Иван", 2, "")])
    rating = calculate_rating([first, second, third])
    assert rating["warnings"] == ["Участника «Петров Пётр» оценил 1 эксперт из 3."]


def test_warning_about_two_of_three():
    first = make_sheet("1.xlsx", "Соколова Н.А.", [("Иванов Иван", 2, "")])
    second = make_sheet("2.xlsx", "Морозов К.В.", [("Иванов Иван", 2, "")])
    third = make_sheet("3.xlsx", "Лебедева О.И.", [("Петров Пётр", 2, "")])
    warnings = calculate_rating([first, second, third])["warnings"]
    assert "Участника «Иванов Иван» оценили 2 эксперта из 3." in warnings


def test_same_expert_in_two_files_gives_warning():
    first = make_sheet("a.xlsx", "Соколова Н.А.", [("Иванов Иван", 2, "")])
    second = make_sheet("b.xlsx", "Соколова Н.А.", [("Иванов Иван", 2, "")])
    warnings = calculate_rating([first, second])["warnings"]
    assert warnings == ["Эксперт «Соколова Н.А.» указан в нескольких файлах: a.xlsx, b.xlsx."]


def test_different_sections_give_warning():
    first = make_sheet("1.xlsx", "Соколова Н.А.", [("Иванов Иван", 2, "")], section="Робототехника")
    second = make_sheet("2.xlsx", "Морозов К.В.", [("Иванов Иван", 2, "")], section="Химия")
    rating = calculate_rating([first, second])
    assert rating["warnings"] == ["Секции в файлах отличаются: «Робототехника», «Химия»."]
    assert rating["section"] == "Робототехника"


def test_advice_is_grouped_by_participant_in_rating_order():
    first = make_sheet("1.xlsx", "Соколова Н.А.", [("Иванов Иван", 2, "Добавьте выводы"), ("Петров Пётр", 3, "")])
    second = make_sheet("2.xlsx", "Морозов К.В.", [("Иванов Иван", 2, "Больше примеров"), ("Петров Пётр", 3, "Отлично")])
    advice = calculate_rating([first, second])["advice"]
    assert [a["fio"] for a in advice] == ["Петров Пётр", "Иванов Иван"]
    assert advice[0]["items"] == [{"expert": "Морозов К.В.", "text": "Отлично"}]
    assert advice[1]["items"] == [
        {"expert": "Соколова Н.А.", "text": "Добавьте выводы"},
        {"expert": "Морозов К.В.", "text": "Больше примеров"},
    ]


def test_experts_and_criteria_are_listed():
    sheet = make_sheet("1.xlsx", "Соколова Н.А.", [("Иванов Иван", 1, "")])
    rating = calculate_rating([sheet, sheet])
    assert rating["experts"][0] == {"name": "Соколова Н.А.", "file": "1.xlsx"}
    assert len(rating["criteria"]) == 12
    assert rating["criteria"][0] == {"short": "Актуальность", "max": 3}
