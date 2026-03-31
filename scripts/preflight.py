from __future__ import annotations

import argparse
import compileall
import subprocess
import sys
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


ROOT = Path(__file__).resolve().parents[1]
DIST_DIR = ROOT / "dist"
DIST_ARCHIVE = DIST_DIR / "function.zip"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run local formatting, linting, tests, and packaging checks.")
    parser.add_argument("command", nargs="?", choices=("check", "format"), default="check")
    args = parser.parse_args()

    if args.command == "format":
        run([sys.executable, "-m", "black", "."])
        return 0

    run([sys.executable, "-m", "black", "--check", "."])
    run([sys.executable, "-m", "ruff", "check", "."])
    run([sys.executable, "-m", "pytest"])
    compile_sources()
    build_lambda_archive()
    print(f"Preflight passed. Package written to {DIST_ARCHIVE}")
    return 0


def run(command: list[str]) -> None:
    print(f"==> {' '.join(command)}")
    subprocess.run(command, cwd=ROOT, check=True)


def compile_sources() -> None:
    print("==> Compiling Python sources")
    lambda_ok = compileall.compile_file(str(ROOT / "lambda_function.py"), quiet=1)
    package_ok = compileall.compile_dir(str(ROOT / "zoey"), quiet=1)

    if not lambda_ok or not package_ok:
        raise SystemExit("Python compilation failed")


def build_lambda_archive() -> None:
    print(f"==> Packaging Lambda into {DIST_ARCHIVE}")
    DIST_DIR.mkdir(parents=True, exist_ok=True)

    if DIST_ARCHIVE.exists():
        DIST_ARCHIVE.unlink()

    with ZipFile(DIST_ARCHIVE, "w", compression=ZIP_DEFLATED) as archive:
        archive.write(ROOT / "lambda_function.py", arcname="lambda_function.py")

        for path in sorted((ROOT / "zoey").rglob("*")):
            if path.is_dir():
                continue
            if should_skip(path):
                continue
            archive.write(path, arcname=path.relative_to(ROOT).as_posix())


def should_skip(path: Path) -> bool:
    if "__pycache__" in path.parts:
        return True
    if path.suffix == ".pyc":
        return True
    return False


if __name__ == "__main__":
    raise SystemExit(main())
