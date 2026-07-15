from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from .warehouse import DATASET_FILES, required_files


DEFAULT_DATASET = "olistbr/brazilian-ecommerce"


def download_olist(data_dir: Path, dataset: str = DEFAULT_DATASET) -> dict[str, Path]:
    data_dir = Path(data_dir)
    try:
        return required_files(data_dir)
    except FileNotFoundError:
        pass
    data_dir.mkdir(parents=True, exist_ok=True)
    command = [
        sys.executable,
        "-m",
        "kaggle",
        "datasets",
        "download",
        "-d",
        dataset,
        "-p",
        str(data_dir),
        "--unzip",
    ]
    try:
        subprocess.run(command, check=True)
    except FileNotFoundError as exc:
        raise RuntimeError("Python could not start the Kaggle CLI. Install the [data] extra first.") from exc
    except subprocess.CalledProcessError as exc:
        raise RuntimeError("Kaggle download failed. Confirm public dataset access and local Kaggle authentication.") from exc
    return required_files(data_dir)


def main() -> None:
    parser = argparse.ArgumentParser(description="Download the public Olist dataset without storing credentials in the repository.")
    parser.add_argument("--data-dir", type=Path, default=Path("data/raw"))
    parser.add_argument("--dataset", default=DEFAULT_DATASET)
    args = parser.parse_args()
    files = download_olist(args.data_dir, args.dataset)
    print("\n".join(str(path) for path in files.values()))


if __name__ == "__main__":
    main()
