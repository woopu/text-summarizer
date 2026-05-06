from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd


@dataclass
class SessionConfig:
    n_sessions: int = 200
    steps_per_session: int = 100
    alpha: float = 0.5
    seed: int = 42
    candidate_pool_size: int = 200


class SharedLinUCB:
    def __init__(self, dim: int, alpha: float) -> None:
        self.alpha = alpha
        self.A = np.eye(dim)
        self.b = np.zeros(dim)

    def score(self, X: np.ndarray) -> np.ndarray:
        a_inv = np.linalg.inv(self.A)
        theta = a_inv @ self.b
        exploit = X @ theta
        explore = np.sqrt(np.sum((X @ a_inv) * X, axis=1))
        return exploit + self.alpha * explore

    def update(self, x: np.ndarray, reward: float) -> None:
        self.A += np.outer(x, x)
        self.b += reward * x


def synthetic_feedback(style_match: bool, rng: np.random.Generator) -> Tuple[int, int, int, float]:
    if style_match:
        adopt = int(rng.random() < 0.70)
        dwell = int(rng.random() < 0.60)
        reject = int(rng.random() < 0.05)
    else:
        adopt = int(rng.random() < 0.10)
        dwell = int(rng.random() < 0.20)
        reject = int(rng.random() < 0.55)
    reward = 1.0 * adopt + 0.3 * dwell - 0.2 * reject
    return adopt, dwell, reject, reward


def run_single_model(model_name: str, model_type: str, X: np.ndarray, items: pd.DataFrame, cfg: SessionConfig) -> pd.DataFrame:
    rng = np.random.default_rng(cfg.seed)
    labels = items["style_label"].to_numpy()
    styles = np.unique(labels)
    linucb = SharedLinUCB(X.shape[1], cfg.alpha) if model_type == "linucb" else None
    pop_rank = np.argsort(-items["pagerank"].fillna(0.0).to_numpy())

    records: List[Dict] = []
    global_step = 0
    for session_id in range(cfg.n_sessions):
        shown = set()
        target_style = rng.choice(styles)
        for within_session_step in range(cfg.steps_per_session):
            unseen = np.array([i for i in range(len(items)) if i not in shown])
            if unseen.size == 0:
                shown.clear()
                unseen = np.arange(len(items))
            pool = rng.choice(unseen, size=min(cfg.candidate_pool_size, unseen.size), replace=False)

            if model_type == "random":
                chosen = int(rng.choice(pool))
            elif model_type == "popularity":
                pool_set = set(pool)
                chosen = int(next(i for i in pop_rank if i in pool_set))
            else:
                chosen = int(pool[np.argmax(linucb.score(X[pool]))])

            shown.add(chosen)
            style_match = labels[chosen] == target_style
            adopt, dwell, reject, reward = synthetic_feedback(style_match, rng)
            if linucb is not None:
                linucb.update(X[chosen], reward)

            records.append({
                "seed": cfg.seed,
                "global_step": global_step,
                "session_id": session_id,
                "within_session_step": within_session_step,
                "model": model_name,
                "image_id": items.iloc[chosen]["image_id"],
                "style_label": labels[chosen],
                "target_style": target_style,
                "adopt": adopt,
                "dwell": dwell,
                "reject": reject,
                "reward": reward,
                "betweenness": float(items.iloc[chosen].get("betweenness", 0.0)),
            })
            global_step += 1

    return pd.DataFrame(records)
