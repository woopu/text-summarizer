from __future__ import annotations

from typing import Dict

import numpy as np
import pandas as pd


def summarize_performance(logs: pd.DataFrame) -> pd.DataFrame:
    perf = logs.groupby("model").agg(
        simulated_ctr=("adopt", "mean"),
        average_reward=("reward", "mean"),
        cumulative_reward=("reward", "sum"),
    ).reset_index()
    random_ctr = float(perf.loc[perf["model"] == "Random", "simulated_ctr"].iloc[0])
    perf["relative_lift_vs_random"] = (perf["simulated_ctr"] - random_ctr) / max(random_ctr, 1e-12)
    return perf


def learning_curve(logs: pd.DataFrame, window: int = 500) -> pd.DataFrame:
    curves = logs[["seed", "global_step", "model", "adopt", "reward"]].copy()
    curves["cum_reward"] = curves.groupby(["seed", "model"])["reward"].cumsum()
    curves["moving_avg_ctr"] = curves.groupby(["seed", "model"])["adopt"].transform(lambda s: s.rolling(window, min_periods=1).mean())
    return curves[["seed", "global_step", "model", "cum_reward", "moving_avg_ctr"]]


def beyond_accuracy(logs: pd.DataFrame, items: pd.DataFrame, top_k: int = 10, bridge_quantile: float = 0.9) -> Dict[str, pd.DataFrame]:
    bridge_cutoff = items["betweenness"].quantile(bridge_quantile)
    bridge_set = set(items.loc[items["betweenness"] >= bridge_cutoff, "image_id"])

    bridge_metrics = logs.groupby("model").apply(lambda d: pd.Series({
        "bridge_exposure_rate": d["image_id"].isin(bridge_set).mean(),
        "bridge_adoption_rate": d.loc[d["image_id"].isin(bridge_set), "adopt"].mean() if d["image_id"].isin(bridge_set).any() else 0.0,
    })).reset_index()

    style_entropy = logs.groupby("model").apply(lambda d: pd.Series({
        "style_entropy": float(-(d["style_label"].value_counts(normalize=True).pipe(lambda p: np.sum(p * np.log2(np.clip(p, 1e-12, None))))))
    })).reset_index()

    coverage = logs.groupby("model")["style_label"].nunique().reset_index(name="exposure_style_coverage")
    early = logs.sort_values("global_step").groupby("model").head(top_k * 50).groupby("model")["style_label"].nunique().reset_index(name="early_exposure_style_coverage")
    coverage = coverage.merge(early, on="model", how="left")

    return {
        "bridge_metrics": bridge_metrics,
        "beyond_accuracy_metrics": style_entropy,
        "style_coverage_results": coverage,
    }
