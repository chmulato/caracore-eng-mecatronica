"""Build the challenge catalog (quiz, case studies and maker missions) from the book."""

import json
import re
import unicodedata
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CHAPTERS_DIR = ROOT / "capitulos"
GLOSSARY_DATA = ROOT / "app" / "data" / "glossario.json"
CONCEPTS_DATA = ROOT / "app" / "data" / "conceitos.json"
OUTPUT_FILE = ROOT / "app" / "data" / "desafios.json"

CHALLENGE_HEADING = re.compile(r"(?m)^###\s+(\U0001F3AE|\U0001F52C)\s*(.+?)\s*$")
LEVEL_BLOCK = re.compile(r"(?m)^\*\*N\u00edvel\s+(\d+)\s*\(([^)]+)\):\s*(.+?)\*\*\s*$")
NEXT_HEADING = re.compile(r"(?m)^#{2,3}\s+")

POINTS = {"quiz": 5, "caso": 10, "missao": 15, "experimento": 20}


def slug(value):
    ascii_text = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"[^a-z0-9]+", "-", ascii_text).strip("-")


def chapter_number(title):
    match = re.match(r"^Cap\u00edtulo\s+(\d+)\s*:", title)
    return int(match.group(1)) if match else None


def read_chapters():
    chapters = []
    for path in sorted(CHAPTERS_DIR.glob("*.md")):
        content = path.read_text(encoding="utf-8")
        heading = re.search(r"(?m)^#\s+(.+?)\s*$", content)
        chapters.append({
            "id": path.stem,
            "title": heading.group(1).strip() if heading else path.stem,
            "content": content,
        })
    return chapters


def build_missions(chapters):
    missions = []
    for chapter in chapters:
        content = chapter["content"]
        for heading in CHALLENGE_HEADING.finditer(content):
            icon = heading.group(1)
            section_title = heading.group(2).strip()
            following = NEXT_HEADING.search(content, heading.end())
            section = content[heading.end():following.start() if following else len(content)]
            levels = list(LEVEL_BLOCK.finditer(section))
            kind = "missao" if icon == "\U0001F3AE" else "experimento"
            if not levels:
                body = section.split("\n---")[0].strip()
                if not body:
                    continue
                missions.append({
                    "id": f"{slug(chapter['id'])}-{slug(section_title)}",
                    "type": kind,
                    "title": section_title,
                    "section": section_title,
                    "level": 1,
                    "difficulty": "Campo",
                    "briefing": body,
                    "chapterId": chapter["id"],
                    "chapterTitle": chapter["title"],
                    "points": POINTS[kind],
                })
                continue
            for index, level in enumerate(levels):
                body_end = levels[index + 1].start() if index + 1 < len(levels) else len(section)
                body = section[level.end():body_end].strip()
                if not body:
                    continue
                mission_title = level.group(3).strip()
                missions.append({
                    "id": f"{slug(chapter['id'])}-{slug(mission_title)}",
                    "type": kind,
                    "title": mission_title,
                    "section": section_title,
                    "level": int(level.group(1)),
                    "difficulty": level.group(2).strip(),
                    "briefing": body,
                    "chapterId": chapter["id"],
                    "chapterTitle": chapter["title"],
                    "points": POINTS[kind] + (5 if level.group(1) == "2" else 0),
                })
    if not missions:
        raise ValueError("No maker missions were found in the chapters.")
    return missions


def pick_distractors(term, pool, count=3):
    """Pick deterministic distractors, preferring terms from the same category."""
    ordered = [item for item in pool if item["id"] != term["id"]]
    same_group = [item for item in ordered if item.get("_category") == term.get("_category")]
    others = [item for item in ordered if item.get("_category") != term.get("_category")]
    start = sum(ord(char) for char in term["id"])
    chosen = []
    for source in (same_group, others):
        if len(chosen) >= count or not source:
            continue
        for offset in range(len(source)):
            candidate = source[(start + offset) % len(source)]
            if candidate["title"] not in [item["title"] for item in chosen]:
                chosen.append(candidate)
            if len(chosen) >= count:
                break
    return chosen[:count]


def build_questions(glossary, categories, chapters):
    category_of = {}
    for category in categories:
        for concept_id in category["concepts"]:
            category_of.setdefault(concept_id, category["id"])
    for term in glossary:
        term["_category"] = category_of.get(term["id"], "geral")

    chapter_by_number = {}
    for chapter in chapters:
        number = chapter_number(chapter["title"])
        if number is not None:
            chapter_by_number[number] = chapter

    questions = []
    specs = [
        ("definition", "quiz", "Qual conceito corresponde a esta defini\u00e7\u00e3o?", "Defini\u00e7\u00e3o"),
        ("analogy", "quiz", "Qual conceito o livro descreve com esta analogia?", "Analogia"),
        ("example", "caso", "Qual conceito resolve a situa\u00e7\u00e3o descrita neste caso?", "Aplica\u00e7\u00e3o"),
    ]
    for term in glossary:
        for field, kind, prompt, facet in specs:
            statement = term.get(field)
            if not statement:
                continue
            distractors = pick_distractors(term, glossary)
            if len(distractors) < 3:
                continue
            options = sorted(
                [term["title"]] + [item["title"] for item in distractors],
                key=slug,
            )
            reference = None
            for chapter_reference in term.get("chapters", []):
                match = re.search(r"(\d+)", chapter_reference)
                if match and int(match.group(1)) in chapter_by_number:
                    reference = chapter_by_number[int(match.group(1))]
                    break
            explanation = term["definition"]
            if field == "definition" and term.get("analogy"):
                explanation = f"{term['definition']} {term['analogy']}"
            questions.append({
                "id": f"{kind}-{field}-{term['id']}",
                "type": kind,
                "conceptId": term["id"],
                "facet": facet,
                "track": term["_category"],
                "prompt": prompt,
                "statement": statement,
                "options": options,
                "answer": options.index(term["title"]),
                "explanation": f"{term['title']}: {explanation}",
                "chapterId": reference["id"] if reference else "",
                "chapterTitle": reference["title"] if reference else "",
                "points": POINTS[kind],
            })
    if not questions:
        raise ValueError("No quiz questions could be generated from the glossary.")
    return questions


def build_tracks(categories, questions, missions):
    tracks = []
    for category in categories:
        items = [question["id"] for question in questions if question["track"] == category["id"]]
        if items:
            tracks.append({
                "id": category["id"],
                "title": category["title"],
                "description": category["description"],
                "items": items,
            })
    tracks.append({
        "id": "campo",
        "title": "Miss\u00f5es de campo",
        "description": "Desafios pr\u00e1ticos e experimentos propostos nos cap\u00edtulos do livro.",
        "items": [mission["id"] for mission in missions],
    })
    return tracks


def main():
    if not GLOSSARY_DATA.exists() or not CONCEPTS_DATA.exists():
        raise FileNotFoundError("Run generate_phase2_data.py before generating the challenges.")

    glossary = json.loads(GLOSSARY_DATA.read_text(encoding="utf-8"))
    concepts = json.loads(CONCEPTS_DATA.read_text(encoding="utf-8"))
    chapters = read_chapters()

    missions = build_missions(chapters)
    questions = build_questions(glossary, concepts["categories"], chapters)
    tracks = build_tracks(concepts["categories"], questions, missions)

    total_points = sum(item["points"] for item in questions) + sum(item["points"] for item in missions)
    levels = [
        {"id": "aprendiz", "title": "Aprendiz de bancada", "minPoints": 0},
        {"id": "tecnico", "title": "T\u00e9cnico de campo", "minPoints": round(total_points * 0.2)},
        {"id": "engenheiro", "title": "Engenheiro rebelde", "minPoints": round(total_points * 0.5)},
        {"id": "mestre", "title": "Mestre da mecatr\u00f4nica", "minPoints": round(total_points * 0.8)},
    ]
    badges = [
        {
            "id": "primeiro-acerto",
            "title": "Primeiro acerto",
            "description": "Acerte a primeira quest\u00e3o de um quiz.",
            "rule": "correctAnswers",
            "threshold": 1,
        },
        {
            "id": "serie-dez",
            "title": "Dez em ordem",
            "description": "Acerte dez quest\u00f5es no total.",
            "rule": "correctAnswers",
            "threshold": 10,
        },
        {
            "id": "analista-de-casos",
            "title": "Analista de casos",
            "description": "Conclua cinco estudos de caso.",
            "rule": "caseAnswers",
            "threshold": 5,
        },
        {
            "id": "maker-iniciado",
            "title": "Maker iniciado",
            "description": "Registre a conclus\u00e3o de uma miss\u00e3o pr\u00e1tica.",
            "rule": "missions",
            "threshold": 1,
        },
        {
            "id": "maker-veterano",
            "title": "Maker veterano",
            "description": "Conclua cinco miss\u00f5es pr\u00e1ticas.",
            "rule": "missions",
            "threshold": 5,
        },
        {
            "id": "trilha-completa",
            "title": "Trilha dominada",
            "description": "Conclua todos os itens de uma trilha.",
            "rule": "completedTracks",
            "threshold": 1,
        },
    ]

    for term in glossary:
        term.pop("_category", None)

    payload = {
        "questions": questions,
        "missions": missions,
        "tracks": tracks,
        "levels": levels,
        "badges": badges,
        "totalPoints": total_points,
    }
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"Generated {len(questions)} questions, {len(missions)} missions, "
        f"{len(tracks)} tracks and {total_points} total points."
    )


if __name__ == "__main__":
    main()
