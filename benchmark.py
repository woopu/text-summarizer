from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable, Dict, Tuple

import numpy as np
import pandas as pd

try:
    import resource
except ImportError:  # non-unix fallback
    resource = None


@dataclass
class BenchmarkResult:
    model: str
    execution_time_sec: float
    throughput_steps_per_sec: float
    memory_mb: float


def _memory_mb() -> float:
    if resource is None:
        return float("nan")
    usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    # Linux ru_maxrss is KB; macOS is bytes
    return usage / 1024.0 if usage > 10_000 else usage / (1024.0 * 1024.0)


def benchmark_model(model_name: str, run_fn: Callable[[], pd.DataFrame]) -> Tuple[pd.DataFrame, BenchmarkResult]:
    mem_before = _memory_mb()
    t0 = time.perf_counter()
    logs = run_fn()
    elapsed = time.perf_counter() - t0
    mem_after = _memory_mb()

    steps = max(len(logs), 1)
    result = BenchmarkResult(
        model=model_name,
        execution_time_sec=elapsed,
        throughput_steps_per_sec=steps / max(elapsed, 1e-12),
        memory_mb=max(mem_after, mem_before),
    )
    return logs, result


def to_frame(results: Dict[str, BenchmarkResult]) -> pd.DataFrame:
    return pd.DataFrame([vars(v) for v in results.values()])
