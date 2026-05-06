#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import pandas as pd


def main() -> None:
    p = argparse.ArgumentParser(description="Build items.csv from Kaggle Interior Design Styles folder layout")
    p.add_argument("--dataset-root", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--class-counts-output", required=True)
    p.add_argument("--dataset-summary-output", default="data/dataset_summary.json")
    args = p.parse_args()

    root = Path(args.dataset_root)
    rows = []
    for style_dir in sorted([d for d in root.iterdir() if d.is_dir()]):
        style = style_dir.name
        for img in sorted(style_dir.glob("*")):
            if img.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
                continue
            rows.append({
                "image_id": img.stem,
                "file_path": str(img),
                "style_label": style,
            })

    items = pd.DataFrame(rows)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    items.to_csv(out, index=False)

    counts = items.groupby("style_label").size().reset_index(name="count")
    c_out = Path(args.class_counts_output)
    c_out.parent.mkdir(parents=True, exist_ok=True)
    counts.to_csv(c_out, index=False)
    summary = {
        "total_images": int(len(items)),
        "n_styles": int(len(counts)),
        "min_class_count": int(counts["count"].min()) if len(counts) else 0,
        "max_class_count": int(counts["count"].max()) if len(counts) else 0,
        "mean_class_count": float(counts["count"].mean()) if len(counts) else 0.0,
        "imbalance_ratio": float((counts["count"].max() / max(counts["count"].min(), 1))) if len(counts) else 0.0,
    }
    summary_path = Path(args.dataset_summary_output)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(f"items: {len(items)} -> {out}")
    print(f"classes: {len(counts)} -> {c_out}")
    print(f"summary -> {summary_path}")


if __name__ == "__main__":
    main()
