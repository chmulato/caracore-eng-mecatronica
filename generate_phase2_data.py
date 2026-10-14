"""Build the local encyclopedia and concept graph from the book glossary."""

import json
import re
import unicodedata
from pathlib import Path


ROOT = Path(__file__).resolve().parent
GLOSSARY_SOURCE = ROOT / "capitulos" / "14_glossario.md"
OUTPUT_DIR = ROOT / "app" / "data"

FIELDS = {
    "Definição": "definition",
    "Analogia": "analogy",
    "Exemplo Prático": "example",
    "Termos Relacionados": "related_titles",
    "Capítulos Relacionados": "chapters",
}

CATEGORIES = [
    {
        "id": "sistemas",
        "title": "Sistemas e CPU",
        "description": "Do processador clássico ao fluxo de execução e às interrupções.",
        "concepts": ["z80", "registrador-register", "program-counter-pc", "stack-pilha-de-memoria",
                     "interrupcao-irq", "nmi-interrupcao-nao-mascaravel", "vetor-de-reset"],
    },
    {
        "id": "eletronica",
        "title": "Controle e eletrônica",
        "description": "Sinais, potência, motores e medições no mundo físico.",
        "concepts": ["ponte-h", "pwm-modulacao-por-largura-de-pulso", "encoder-optico"],
    },
    {
        "id": "robotica",
        "title": "Robótica e navegação",
        "description": "Percepção, localização e comunicação entre os componentes do robô.",
        "concepts": ["lidar", "encoder-optico", "odometria", "slam-localizacao-e-mapeamento-simultaneos",
                     "filtro-de-kalman", "ros-2-robot-operating-system", "nos-nodes"],
    },
    {
        "id": "matematica",
        "title": "Matemática e otimização",
        "description": "Representar espaço, estimar estados e organizar cargas.",
        "concepts": ["odometria", "filtro-de-kalman", "matriz-booleana-de-ocupacao", "3d-bin-packing"],
    },
    {
        "id": "software",
        "title": "Software e arquitetura",
        "description": "Como instruções, processos e sistemas conectados coordenam ações.",
        "concepts": ["program-counter-pc", "stack-pilha-de-memoria", "interrupcao-irq", "nmi-interrupcao-nao-mascaravel",
                     "vetor-de-reset", "ros-2-robot-operating-system", "nos-nodes"],
    },
]


def slug(value):
    normalized = unicodedata.normalize("NFKD", value)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"[^a-z0-9]+", "-", ascii_text).strip("-")


def parse_glossary(source):
    matches = list(re.finditer(r"(?m)^###\s+\d+\.\s+(.+?)\s*$", source))
    entries = []
    for index, match in enumerate(matches):
        section_end = matches[index + 1].start() if index + 1 < len(matches) else len(source)
        body = source[match.end():section_end]
        heading = re.sub(r"\s+\([^)]*\)\s*$", "", match.group(1)).strip()
        entry = {
            "id": slug(heading),
            "title": heading,
            "definition": "",
            "analogy": "",
            "example": "",
            "related_titles": [],
            "chapters": [],
        }
        for line in body.splitlines():
            field = re.match(r"^\s*\*\s+\*\*(.+?):\*\*\s*(.*)$", line)
            if not field:
                continue
            label, value = field.groups()
            key = FIELDS.get(label.strip())
            if not key:
                continue
            if key == "related_titles":
                entry[key] = [term.strip() for term in value.split(",") if term.strip()]
            elif key == "chapters":
                entry[key] = [part.strip() for part in re.split(r"[,;]", value) if part.strip()]
            else:
                entry[key] = value.strip()
        if not entry["definition"]:
            raise ValueError(f"Glossary entry has no definition: {heading}")
        entries.append(entry)
    if not entries:
        raise ValueError(f"No glossary entries found in {GLOSSARY_SOURCE}")
    return entries


def link_related_terms(entries):
    lookup = {}
    for entry in entries:
        lookup[slug(entry["title"])] = entry["id"]
        for alias in entry["title"].split("/"):
            lookup[slug(alias)] = entry["id"]

    for entry in entries:
        entry["related"] = []
        for title in entry.pop("related_titles"):
            related_id = lookup.get(slug(title))
            if related_id and related_id != entry["id"] and related_id not in entry["related"]:
                entry["related"].append(related_id)
    return entries


def main():
    source = GLOSSARY_SOURCE.read_text(encoding="utf-8")
    entries = link_related_terms(parse_glossary(source))
    entry_ids = {entry["id"] for entry in entries}
    for category in CATEGORIES:
        missing = set(category["concepts"]) - entry_ids
        if missing:
            raise ValueError(f"Unknown concepts in category {category['id']}: {sorted(missing)}")

    connections = []
    seen = set()
    for entry in entries:
        for related_id in entry["related"]:
            pair = tuple(sorted((entry["id"], related_id)))
            if pair not in seen:
                seen.add(pair)
                connections.append({"from": entry["id"], "to": related_id})

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    encyclopedia_file = OUTPUT_DIR / "glossario.json"
    concepts_file = OUTPUT_DIR / "conceitos.json"
    encyclopedia_file.write_text(
        json.dumps(entries, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    concepts_file.write_text(
        json.dumps({"categories": CATEGORIES, "connections": connections}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Generated {len(entries)} glossary entries and {len(connections)} concept connections.")


if __name__ == "__main__":
    main()
