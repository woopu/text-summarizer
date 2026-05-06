#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path

import networkx as nx
import numpy as np
import pandas as pd

from benchmark import benchmark_model
from metrics import beyond_accuracy, learning_curve, summarize_performance
from simulation import SessionConfig, run_single_model


@dataclass
class PipelineConfig:
    n_sessions: int = 200
    steps_per_session: int = 100
    total_steps_per_seed: int = 20000
    alpha: float = 0.5
    seed: int = 42
    seeds: list[int] | None = None
    use_mock_features: bool = False
    skip_cosine_sim_save: bool = False
    compress_output: bool = False
    candidate_pool_size: int = 200
    similarity_threshold: float = 0.85
    top_k: int = 10


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--items", required=True)
    p.add_argument("--features-raw", default="")
    p.add_argument("--features-pca", default="")
    p.add_argument("--graph-priors", default="")
    p.add_argument("--output-dir", default="outputs")
    p.add_argument("--generate-mock-features", action="store_true")
    p.add_argument("--alpha", type=float, default=0.5)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--seeds", type=int, nargs="*", default=None)
    p.add_argument("--n-sessions", type=int, default=200)
    p.add_argument("--steps-per-session", type=int, default=100)
    p.add_argument("--skip-cosine-sim-save", action="store_true", help="Do not save cosine_sim.npy (useful for Drive storage).")
    p.add_argument("--compress-output", action="store_true", help="Zip the output directory after the run finishes.")
    return p.parse_args()


def load_items(path: Path) -> pd.DataFrame:
    items = pd.read_csv(path)
    if "style_label" not in items.columns and "style_label_19" in items.columns:
        items = items.rename(columns={"style_label_19": "style_label"})
    if "style_label" not in items.columns:
        raise ValueError("items.csv must include style_label or style_label_19")
    return items


def load_or_mock_features(n: int, raw_path: str, pca_path: str, seed: int, use_mock: bool):
    if raw_path and pca_path:
        return np.load(raw_path), np.load(pca_path)
    if not use_mock:
        raise ValueError("missing feature files; use --generate-mock-features")
    rng = np.random.default_rng(seed)
    raw = rng.normal(0, 1, (n, 671)).astype(np.float32)
    pca = raw[:, :50]
    return raw, pca


def build_graph(raw: np.ndarray, threshold: float):
    norm = raw / np.clip(np.linalg.norm(raw, axis=1, keepdims=True), 1e-12, None)
    cosine_sim = norm @ norm.T
    np.fill_diagonal(cosine_sim, 0.0)
    src, dst = np.where(cosine_sim > threshold)
    edges = pd.DataFrame({"src": src, "dst": dst, "weight": cosine_sim[src, dst]})
    edges = edges[edges["src"] < edges["dst"]].reset_index(drop=True)

    g = nx.Graph()
    g.add_nodes_from(range(len(raw)))
    g.add_weighted_edges_from(edges[["src", "dst", "weight"]].itertuples(index=False, name=None))

    stats = pd.DataFrame([{
        "num_nodes": g.number_of_nodes(),
        "num_edges": g.number_of_edges(),
        "density": nx.density(g),
        "average_degree": np.mean([d for _, d in g.degree()]) if g.number_of_nodes() else 0.0,
        "num_components": nx.number_connected_components(g),
        "largest_component_ratio": max([len(c) for c in nx.connected_components(g)], default=0) / max(g.number_of_nodes(), 1),
        "threshold": threshold,
    }])
    return cosine_sim, edges, stats, g


def graph_priors(g: nx.Graph, cosine_sim: np.ndarray) -> pd.DataFrame:
    pr = nx.pagerank(g) if g.number_of_edges() else {n: 0.0 for n in g.nodes()}
    bc = nx.betweenness_centrality(g, k=min(200, max(g.number_of_nodes()-1, 1)), seed=42) if g.number_of_nodes() > 2 else {n: 0.0 for n in g.nodes()}
    rows = []
    for n in g.nodes():
        neighbors = list(g.neighbors(n))
        rows.append({
            "idx": n,
            "pagerank": pr[n],
            "neighbor_avg_similarity": float(np.mean([cosine_sim[n, m] for m in neighbors])) if neighbors else 0.0,
            "betweenness": bc[n],
            "degree": g.degree(n),
        })
    return pd.DataFrame(rows)


def main() -> None:
    args = parse_args()
    seed_list = args.seeds if args.seeds else [args.seed]
    cfg = PipelineConfig(
        n_sessions=args.n_sessions,
        steps_per_session=args.steps_per_session,
        total_steps_per_seed=args.n_sessions * args.steps_per_session,
        alpha=args.alpha,
        seed=args.seed,
        seeds=seed_list,
        use_mock_features=bool(args.generate_mock_features),
        skip_cosine_sim_save=bool(args.skip_cosine_sim_save),
        compress_output=bool(args.compress_output),
    )
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    items = load_items(Path(args.items)).reset_index(drop=True)
    raw, pca = load_or_mock_features(len(items), args.features_raw, args.features_pca, cfg.seed, args.generate_mock_features)
    cosine_sim, edges, graph_stats, graph = build_graph(raw, cfg.similarity_threshold)

    priors = pd.read_csv(args.graph_priors) if args.graph_priors else graph_priors(graph, cosine_sim)
    items["idx"] = np.arange(len(items))
    items = items.merge(priors, on="idx", how="left")

    feature_sets = {
        "visual_only": pca,
        "visual_pagerank": np.column_stack([pca, items[["pagerank"]].to_numpy()]),
        "visual_simgraph": np.column_stack([pca, items[["neighbor_avg_similarity"]].to_numpy()]),
        "visual_bridge": np.column_stack([pca, items[["betweenness"]].to_numpy()]),
        "full_graph": np.column_stack([pca, items[["pagerank", "neighbor_avg_similarity", "betweenness"]].to_numpy()]),
    }

    specs = {
        "Random": ("random", feature_sets["visual_only"]),
        "Popularity/PageRank": ("popularity", feature_sets["visual_only"]),
        "Visual-only LinUCB": ("linucb", feature_sets["visual_only"]),
        "PageRank-LinUCB": ("linucb", feature_sets["visual_pagerank"]),
        "SimGraph-LinUCB": ("linucb", feature_sets["visual_simgraph"]),
        "Bridge-LinUCB": ("linucb", feature_sets["visual_bridge"]),
        "Full Graph-Enhanced LinUCB": ("linucb", feature_sets["full_graph"]),
    }

    all_logs = []
    all_perf = []
    benchmark_rows = []
    for seed in seed_list:
        sim_cfg = SessionConfig(n_sessions=args.n_sessions, steps_per_session=args.steps_per_session, alpha=cfg.alpha, seed=seed, candidate_pool_size=cfg.candidate_pool_size)
        benchmark_logs = []
        for n, (mt, X) in specs.items():
            one_log, row = benchmark_model(n, lambda n=n, mt=mt, X=X: run_single_model(n, mt, X, items, sim_cfg))
            one_log["seed"] = seed
            benchmark_logs.append(one_log)
            benchmark_rows.append({"model": n, "seed": seed, "execution_time_sec": row.execution_time_sec, "memory_mb": row.memory_mb, "throughput_steps_per_sec": row.throughput_steps_per_sec})
        logs_seed = pd.concat(benchmark_logs, ignore_index=True)
        all_logs.append(logs_seed)
        perf_seed = summarize_performance(logs_seed)
        perf_seed["seed"] = seed
        all_perf.append(perf_seed)
    logs = pd.concat(all_logs, ignore_index=True)
    perf_by_seed = pd.concat(all_perf, ignore_index=True)
    perf = perf_by_seed.groupby("model")[["simulated_ctr", "average_reward", "cumulative_reward", "relative_lift_vs_random"]].mean().reset_index()
    curves = learning_curve(logs)
    more = beyond_accuracy(logs, items, top_k=cfg.top_k)

    (out / "config.json").write_text(json.dumps(asdict(cfg), indent=2), encoding="utf-8")
    if not args.skip_cosine_sim_save:
        np.save(out / "cosine_sim.npy", cosine_sim)
    edges.to_csv(out / "graph_edges.csv", index=False)
    graph_stats.to_csv(out / "graph_stats.csv", index=False)
    priors.to_csv(out / "graph_priors.csv", index=False)
    perf.to_csv(out / "offline_performance_results.csv", index=False)
    perf_by_seed.to_csv(out / "offline_performance_by_seed.csv", index=False)
    summary_rows = []
    metrics = ["simulated_ctr", "average_reward", "cumulative_reward", "relative_lift_vs_random"]
    for model, g in perf_by_seed.groupby("model"):
        for m in metrics:
            arr = g[m].to_numpy()
            mean = float(np.mean(arr))
            std = float(np.std(arr, ddof=1)) if len(arr) > 1 else 0.0
            ci = 1.96 * std / math.sqrt(len(arr)) if len(arr) > 1 else 0.0
            summary_rows.append({"model": model, "metric": m, "mean": mean, "std": std, "n": int(len(arr)), "ci95_low": mean - ci, "ci95_high": mean + ci})
    pd.DataFrame(summary_rows).to_csv(out / "offline_performance_summary.csv", index=False)
    perf[perf["model"].str.contains("LinUCB")].to_csv(out / "ablation_results.csv", index=False)
    pd.DataFrame(benchmark_rows).to_csv(out / "benchmark_results.csv", index=False)
    curves.to_csv(out / "learning_curves.csv", index=False)
    more["beyond_accuracy_metrics"].to_csv(out / "beyond_accuracy_metrics.csv", index=False)
    more["bridge_metrics"].to_csv(out / "bridge_metrics.csv", index=False)
    more["style_coverage_results"].to_csv(out / "style_coverage_results.csv", index=False)
    logs.to_csv(out / "recommendation_event_logs.csv", index=False)

    # case-study summary: compare baseline vs main model
    baseline_ctr = float(perf.loc[perf["model"] == "Visual-only LinUCB", "simulated_ctr"].iloc[0])
    full_ctr = float(perf.loc[perf["model"] == "Full Graph-Enhanced LinUCB", "simulated_ctr"].iloc[0])
    lift = (full_ctr - baseline_ctr) / max(baseline_ctr, 1e-12) * 100
    case_text = (
        "# Case Analysis (Auto-generated)\n\n"
        "## Scenario\n"
        "Session-level interior style exploration with image-only cold-start setting.\n\n"
        "## Baseline vs Proposed Comparison\n"
        f"- Baseline (Visual-only LinUCB CTR): {baseline_ctr:.4f}\n"
        f"- Proposed (Full Graph-Enhanced LinUCB CTR): {full_ctr:.4f}\n"
        f"- Relative difference: {lift:.2f}%\n\n"
        "## Observation\n"
        + (
            "The graph-enhanced model achieved higher simulated CTR than the visual-only baseline in this repeated-seed summary.\n"
            if full_ctr > baseline_ctr else
            "The graph-enhanced model achieved lower simulated CTR than the visual-only baseline in this repeated-seed summary.\n"
            if full_ctr < baseline_ctr else
            "No simulated CTR difference was observed between the two models in this repeated-seed summary.\n"
        )
        + "\nThis case analysis is descriptive and does not replace aggregate benchmarking or repeated-seed evaluation.\n"
    )
    (out / "case_analysis_report.md").write_text(case_text, encoding="utf-8")

    manifest = []
    for path in sorted(out.iterdir()):
        if path.is_file():
            manifest.append({"file": path.name, "size_bytes": path.stat().st_size})
    (out / "output_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    if args.compress_output:
        shutil.make_archive(str(out), "zip", root_dir=out)


if __name__ == "__main__":
    main()
