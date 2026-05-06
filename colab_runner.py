#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


DEFAULT_PROJECT_DIR = "/content/drive/MyDrive/thesis_recommender"
SCRIPT_DIR = Path(__file__).resolve().parent


def run_command(cmd: list[str]) -> None:
    print("\n$ " + " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Colab-friendly launcher for smoke/formal recommendation benchmark runs.")
    parser.add_argument("--project-dir", default=DEFAULT_PROJECT_DIR, help="Google Drive project directory.")
    parser.add_argument("--mode", choices=["smoke", "formal"], default="smoke")
    parser.add_argument("--n-sessions", type=int, default=50)
    parser.add_argument("--steps-per-session", type=int, default=100)
    parser.add_argument("--seeds", type=int, nargs="*", default=None)
    parser.add_argument("--output-name", default="")
    parser.add_argument("--dataset-root", default="")
    parser.add_argument("--features-raw", default="")
    parser.add_argument("--features-pca", default="")
    parser.add_argument("--skip-cosine-sim-save", action="store_true")
    parser.add_argument("--compress-output", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    project_dir = Path(args.project_dir)
    data_dir = project_dir / "data"
    outputs_dir = project_dir / "outputs"
    data_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    output_name = args.output_name or ("smoke" if args.mode == "smoke" else "formal_v1")
    output_dir = outputs_dir / output_name

    if args.mode == "smoke":
        items_path = data_dir / "demo_items.csv"
        run_command([
            sys.executable,
            str(SCRIPT_DIR / "make_demo_items.py"),
            "--output",
            str(items_path),
            "--n-items",
            "3729",
            "--n-styles",
            "19",
            "--seed",
            "42",
        ])
        pipeline_cmd = [
            sys.executable,
            str(SCRIPT_DIR / "run_pipeline.py"),
            "--items",
            str(items_path),
            "--generate-mock-features",
            "--n-sessions",
            str(args.n_sessions),
            "--steps-per-session",
            str(args.steps_per_session),
            "--output-dir",
            str(output_dir),
        ]
    else:
        dataset_root = Path(args.dataset_root) if args.dataset_root else data_dir / "interior-design-styles"
        items_path = data_dir / "items.csv"
        run_command([
            sys.executable,
            str(SCRIPT_DIR / "build_items_from_dataset.py"),
            "--dataset-root",
            str(dataset_root),
            "--output",
            str(items_path),
            "--class-counts-output",
            str(data_dir / "class_counts.csv"),
            "--dataset-summary-output",
            str(data_dir / "dataset_summary.json"),
        ])
        features_raw = Path(args.features_raw) if args.features_raw else data_dir / "features_671.npy"
        features_pca = Path(args.features_pca) if args.features_pca else data_dir / "features_pca50.npy"
        for feature_path in [features_raw, features_pca]:
            if not feature_path.exists():
                raise FileNotFoundError(f"Missing feature file: {feature_path}")
        pipeline_cmd = [
            sys.executable,
            str(SCRIPT_DIR / "run_pipeline.py"),
            "--items",
            str(items_path),
            "--features-raw",
            str(features_raw),
            "--features-pca",
            str(features_pca),
            "--n-sessions",
            str(args.n_sessions),
            "--steps-per-session",
            str(args.steps_per_session),
            "--output-dir",
            str(output_dir),
        ]
        if args.seeds:
            pipeline_cmd.extend(["--seeds", *[str(seed) for seed in args.seeds]])

    if args.skip_cosine_sim_save:
        pipeline_cmd.append("--skip-cosine-sim-save")
    if args.compress_output:
        pipeline_cmd.append("--compress-output")

    run_command(pipeline_cmd)
    print(f"\nDone. Outputs saved to: {output_dir}")
    if args.compress_output:
        print(f"Compressed archive saved to: {output_dir}.zip")


if __name__ == "__main__":
    main()
