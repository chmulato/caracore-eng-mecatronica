"""Build the official website and copy the production PWA into docs/app."""

import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
APP_SOURCE = ROOT / "app"
APP_TARGET = ROOT / "docs" / "app"


def run(script):
    subprocess.run([sys.executable, str(ROOT / script)], cwd=ROOT, check=True)


def main():
    for script in (
        "generate_app_data.py",
        "generate_phase2_data.py",
        "generate_phase3_data.py",
        "compile_html.py",
    ):
        run(script)

    if APP_TARGET.exists():
        shutil.rmtree(APP_TARGET)
    shutil.copytree(APP_SOURCE, APP_TARGET, ignore=shutil.ignore_patterns("README.md"))
    print(f"PWA publicada em: {APP_TARGET}")


if __name__ == "__main__":
    main()
