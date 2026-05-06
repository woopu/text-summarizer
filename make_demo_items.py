#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import numpy as np
import pandas as pd


def main() -> None:
    p = argparse.ArgumentParser(description="Create demo items.csv for pipeline evaluation")
    p.add_argument("--output", default="data/items.csv")
    p.add_argument("--n-items", type=int, default=3729)
    p.add_argument("--n-styles", type=int, default=19)
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()

    rng = np.random.default_rng(args.seed)
    styles = [f"style_{i:02d}" for i in range(args.n_styles)]
    df = pd.DataFrame({
        "image_id": [f"img_{i:05d}" for i in range(args.n_items)],
        "file_path": [f"images/img_{i:05d}.jpg" for i in range(args.n_items)],
        "style_label": rng.choice(styles, size=args.n_items),
    })

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    print(f"wrote {len(df)} rows -> {out}")


if __name__ == "__main__":
    main()
