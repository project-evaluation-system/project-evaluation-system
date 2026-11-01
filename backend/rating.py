from criteria import CRITERIA, normalize


def collect_scores(sheets):
    """Собирает баллы по участникам из всех файлов. Участник определяется по normalize(ФИО)."""
    participants = {}
    for sheet in sheets:
        for row in sheet["rows"]:
            key = normalize(row["fio"])
            if key not in participants:
                participants[key] = {
                    "fio": row["fio"],
                    "count": 0,
                    "scores": {short: [] for short, _, _, _ in CRITERIA},
                }
            participants[key]["count"] += 1
            for short, value in row["scores"].items():
                participants[key]["scores"][short].append(value)
    return participants


def calculate_rating(sheets):
    results = []
    for item in collect_scores(sheets).values():
        averages = {short: sum(values) / len(values) for short, values in item["scores"].items()}
        results.append({
            "place": 0,
            "fio": item["fio"],
            "total": sum(averages.values()),
            "experts_count": item["count"],
            "criteria": averages,
        })

    results.sort(key=lambda r: (-round(r["total"], 2), normalize(r["fio"])))
    for number, result in enumerate(results, start=1):
        result["place"] = number

    sections = [sheet["section"] for sheet in sheets if sheet["section"]]
    return {
        "section": sections[0] if sections else "",
        "experts": [{"name": sheet["expert"], "file": sheet["file"]} for sheet in sheets],
        "criteria": [{"short": short, "max": max_score} for short, _, max_score, _ in CRITERIA],
        "results": results,
    }
