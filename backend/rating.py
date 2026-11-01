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


def collect_advice(sheets, results):
    advice = []
    for result in results:
        items = []
        for sheet in sheets:
            for row in sheet["rows"]:
                if normalize(row["fio"]) == normalize(result["fio"]) and row["comment"]:
                    items.append({"expert": sheet["expert"], "text": row["comment"]})
        if items:
            advice.append({"fio": result["fio"], "items": items})
    return advice


def collect_warnings(sheets, results):
    warnings = []
    total = len(sheets)

    for result in results:
        count = result["experts_count"]
        if count < total:
            if count == 1:
                warnings.append(f"Участника «{result['fio']}» оценил 1 эксперт из {total}.")
            else:
                warnings.append(f"Участника «{result['fio']}» оценили {count} эксперта из {total}.")

    files_by_expert = {}
    names = {}
    for sheet in sheets:
        key = normalize(sheet["expert"])
        names.setdefault(key, sheet["expert"])
        files_by_expert.setdefault(key, []).append(sheet["file"])
    for key, files in files_by_expert.items():
        if len(files) > 1:
            warnings.append(f"Эксперт «{names[key]}» указан в нескольких файлах: {', '.join(files)}.")

    sections = {}
    for sheet in sheets:
        if sheet["section"]:
            sections.setdefault(normalize(sheet["section"]), sheet["section"])
    if len(sections) > 1:
        names_text = "», «".join(sections.values())
        warnings.append(f"Секции в файлах отличаются: «{names_text}».")

    return warnings


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
        previous = results[number - 2] if number > 1 else None
        if previous and round(previous["total"], 2) == round(result["total"], 2):
            result["place"] = previous["place"]
        else:
            result["place"] = number

    sections = [sheet["section"] for sheet in sheets if sheet["section"]]
    return {
        "section": sections[0] if sections else "",
        "experts": [{"name": sheet["expert"], "file": sheet["file"]} for sheet in sheets],
        "criteria": [{"short": short, "max": max_score} for short, _, max_score, _ in CRITERIA],
        "results": results,
        "advice": collect_advice(sheets, results),
        "warnings": collect_warnings(sheets, results),
    }
