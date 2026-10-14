"""Generate the PWA chapter index directly from the Markdown source files."""

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CHAPTERS_DIR = ROOT / "capitulos"
OUTPUT_FILE = ROOT / "app" / "data" / "capitulos.json"


def main():
    if not CHAPTERS_DIR.is_dir():
        raise FileNotFoundError(f"Chapter source directory not found: {CHAPTERS_DIR}")

    chapters = []
    for path in sorted(CHAPTERS_DIR.glob("*.md")):
        content = path.read_text(encoding="utf-8").strip()
        heading = re.search(r"(?m)^#\s+(.+?)\s*$", content)
        title = heading.group(1).strip() if heading else path.stem.replace("_", " ")
        chapters.append(
            {
                "id": path.stem,
                "title": title,
                "source": f"capitulos/{path.name}",
                "content": content,
            }
        )

    if not chapters:
        raise RuntimeError(f"No Markdown chapters found in {CHAPTERS_DIR}")

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(
        json.dumps(chapters, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Generated {len(chapters)} chapters in {OUTPUT_FILE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
