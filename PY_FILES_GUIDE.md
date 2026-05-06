# `.py` 檔案怎麼用？

這份專案的 Python 檔案可以分成三層：

1. **Colab / 指令入口**：你會直接執行。
2. **資料準備工具**：用來產生 `items.csv` 或 demo data。
3. **內部模組**：通常不用直接跑，由 `run_pipeline.py` 呼叫。

---

## 最推薦：Colab 只先用這 1 個入口

### `colab_runner.py`

**用途**：Colab 主要入口。它會幫你呼叫其他 `.py`，分成 smoke / formal 兩種模式。

### Smoke test

```bash
python colab_runner.py \
  --project-dir "$PROJECT_DIR" \
  --mode smoke \
  --n-sessions 50 \
  --steps-per-session 100 \
  --output-name smoke \
  --skip-cosine-sim-save \
  --compress-output
```

### Formal run

```bash
python colab_runner.py \
  --project-dir "$PROJECT_DIR" \
  --mode formal \
  --n-sessions 1000 \
  --steps-per-session 120 \
  --seeds 1 2 3 4 5 6 7 8 9 10 \
  --output-name formal_v1 \
  --skip-cosine-sim-save \
  --compress-output
```

> **Colab 裡優先用這個。**除非你要 debug，否則不需要手動跑下面每一支。

---

## 你可能會直接執行的工具

### `run_pipeline.py`

**用途**：核心實驗管線。它會讀 items/features、建 graph、算 priors、跑模型、輸出所有 CSV/JSON/MD 結果。

通常由 `colab_runner.py` 呼叫；若手動跑 formal benchmark：

```bash
python run_pipeline.py \
  --items "$PROJECT_DIR/data/items.csv" \
  --features-raw "$PROJECT_DIR/data/features_671.npy" \
  --features-pca "$PROJECT_DIR/data/features_pca50.npy" \
  --n-sessions 1000 \
  --steps-per-session 120 \
  --seeds 1 2 3 4 5 6 7 8 9 10 \
  --output-dir "$PROJECT_DIR/outputs/formal_v1" \
  --skip-cosine-sim-save \
  --compress-output
```

---

### `build_items_from_dataset.py`

**用途**：把 Kaggle Interior Design Styles 的資料夾結構轉成正式 `items.csv`。

```bash
python build_items_from_dataset.py \
  --dataset-root "$PROJECT_DIR/data/interior-design-styles" \
  --output "$PROJECT_DIR/data/items.csv" \
  --class-counts-output "$PROJECT_DIR/data/class_counts.csv" \
  --dataset-summary-output "$PROJECT_DIR/data/dataset_summary.json"
```

輸出：

- `items.csv`
- `class_counts.csv`
- `dataset_summary.json`

---

### `make_demo_items.py`

**用途**：產生假的 `items.csv` 給 smoke test 用。

```bash
python make_demo_items.py \
  --output "$PROJECT_DIR/data/demo_items.csv" \
  --n-items 3729 \
  --n-styles 19 \
  --seed 42
```

> 這只用於 smoke test / pipeline debugging，不是正式論文資料。

---

### `evaluate_pipeline.sh`

**用途**：本機或 bash 環境的一鍵 smoke test。

```bash
./evaluate_pipeline.sh 50 100 outputs_smoke
```

> Colab 也可以用，但 Colab 最推薦還是 `colab_runner.py`。

---

## 通常不用直接執行的內部模組

### `simulation.py`

**用途**：定義 session-level simulation 與 LinUCB。

包含：

- `SessionConfig`
- `SharedLinUCB`
- `synthetic_feedback()`
- `run_single_model()`

你通常不用直接跑它；`run_pipeline.py` 會呼叫它。

---

### `metrics.py`

**用途**：計算輸出指標。

包含：

- `summarize_performance()`
- `learning_curve()`
- `beyond_accuracy()`

你通常不用直接跑它；`run_pipeline.py` 會呼叫它並輸出 CSV。

---

### `benchmark.py`

**用途**：測每個模型的 runtime diagnostics。

包含：

- `benchmark_model()`
- `BenchmarkResult`

你通常不用直接跑它；`run_pipeline.py` 會呼叫它並輸出 `benchmark_results.csv`。

---

### `recommender_pipeline.py`

**用途**：舊入口相容檔。

它只是呼叫 `run_pipeline.py` 的 `main()`。新流程建議直接用：

```bash
python run_pipeline.py ...
```

或 Colab 用：

```bash
python colab_runner.py ...
```

---

### `text-summarizer.py`

**用途**：舊的文字摘要範例，和目前 Graph-Enhanced LinUCB 推薦實驗無關。

> 做論文推薦系統實驗時可以忽略它。

---

## 總結：你在 Colab 實際會用哪幾個？

| 目的 | 你要用的檔案 |
|---|---|
| 一格一格貼 Colab | `COLAB_BLOCKS.md` |
| Colab smoke / formal 主入口 | `colab_runner.py` |
| 手動正式 pipeline | `run_pipeline.py` |
| 建正式 items.csv | `build_items_from_dataset.py` |
| 建 smoke demo items | `make_demo_items.py` |
| 本機 smoke test | `evaluate_pipeline.sh` |
| 內部 simulation | `simulation.py`（不用直接跑） |
| 內部 metrics | `metrics.py`（不用直接跑） |
| 內部 benchmark | `benchmark.py`（不用直接跑） |
