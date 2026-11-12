"""Package console entrypoint for Agents-kit CLI."""

import runpy
from pathlib import Path


def main() -> None:
    kit_cli = Path(__file__).resolve().parent.parent / "bin" / "agents-kit"
    runpy.run_path(str(kit_cli), run_name="__main__")


if __name__ == "__main__":
    main()
