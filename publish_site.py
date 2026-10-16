"""Build the official website and copy the production PWA into docs/app."""

import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
APP_SOURCE = ROOT / "app"
APP_TARGET = ROOT / "docs" / "app"


def run(script):
    subprocess.run([sys.executable, str(ROOT / script)], cwd=ROOT, check=True)


def _make_writable(path):
    if path.is_dir():
        for root, dirs, files in os.walk(path):
            for name in dirs + files:
                full_path = Path(root) / name
                try:
                    os.chmod(full_path, os.stat(full_path).st_mode | stat.S_IWRITE)
                except OSError:
                    pass
    else:
        try:
            os.chmod(path, os.stat(path).st_mode | stat.S_IWRITE)
        except OSError:
            pass


def remove_tree(path):
    if not path.exists():
        return

    _make_writable(path)

    def _onerror(func, exc_path, exc_info):
        if not os.path.exists(exc_path):
            return
        _make_writable(Path(exc_path))
        try:
            func(exc_path)
        except OSError:
            os.chmod(exc_path, stat.S_IWRITE)
            if os.path.isdir(exc_path):
                os.rmdir(exc_path)
            else:
                os.remove(exc_path)

    shutil.rmtree(path, onerror=_onerror)


def main():
    for script in (
        "generate_app_data.py",
        "generate_phase2_data.py",
        "generate_phase3_data.py",
        "compile_html.py",
    ):
        run(script)

    remove_tree(APP_TARGET)
    shutil.copytree(APP_SOURCE, APP_TARGET, ignore=shutil.ignore_patterns("README.md"))
    print(f"PWA publicada em: {APP_TARGET}")


if __name__ == "__main__":
    main()
