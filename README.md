## 如何在 Google Colab 跑（Recommendation Benchmark + Case Analysis）

本專案用於評估 Graph-Enhanced LinUCB 在室內風格早期探索情境中的 synthetic session-based 推薦表現。Colab 版本的重點是：**把資料、features、正式 outputs 存到 Google Drive，不要因為 runtime 重開而重跑正式實驗。**




## 怎麼把 `.py` 給 Colab 跑？

如果你不確定 `.py` 檔案要怎麼放進 Colab，請看：[`COLAB_UPLOAD_GUIDE.md`](COLAB_UPLOAD_GUIDE.md)。

最推薦做法：把整個 repo 資料夾上傳到 Google Drive 的 `MyDrive/thesis_recommender/`，Colab 只要 `cd` 到該資料夾後用 `python colab_runner.py ...` 執行，不需要把 `.py` 一個一個貼進 notebook。

## `.py` 檔案使用說明

如果你不知道每個 Python 檔案要怎麼用，請看：[`PY_FILES_GUIDE.md`](PY_FILES_GUIDE.md)。

最簡單原則：Colab 先用 `colab_runner.py`；只有 debug 或手動正式跑時才直接用 `run_pipeline.py`。

## Colab 一格一格貼上版本

如果你想照 Colab cell 一格一格執行，請看：[`COLAB_BLOCKS.md`](COLAB_BLOCKS.md)。

建議順序：

1. Block 0–4：先跑 smoke test。
2. Block 5–8：確認正式資料與 features 後跑 formal benchmark。
3. Block 9：Colab 重開後只讀舊結果，不重跑正式實驗。

## 1. Colab setup

```python
from google.colab import drive
drive.mount('/content/drive')
```

```bash
PROJECT_DIR=/content/drive/MyDrive/thesis_recommender
cd "$PROJECT_DIR"
pip install -r requirements.txt
mkdir -p "$PROJECT_DIR/data" "$PROJECT_DIR/outputs"
```

> 注意：以下指令假設本 repo 已放在 `$PROJECT_DIR`，且目前工作目錄已切換到 repo 根目錄。`colab_runner.py` 會使用自身檔案位置尋找同 repo 內的其他腳本，因此從其他目錄呼叫也能正常找到 pipeline scripts。

## 2. Colab smoke test（只用來確認 pipeline 可跑）

建議先跑小規模 smoke test，輸出會直接存到 Google Drive：

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

> `make_demo_items.py` 與 `--generate-mock-features` 僅供 smoke testing / pipeline debugging。正式論文結果必須使用 Kaggle Interior Design Styles 圖片所萃取的真實 visual features。
> `--skip-cosine-sim-save` 只是不把 `cosine_sim.npy` 寫入 Google Drive；pipeline 仍會在記憶體中計算 similarity matrix。

## 3. Colab formal run（正式論文結果）

請先把 Kaggle dataset 與 feature 檔放在：

```text
$PROJECT_DIR/data/interior-design-styles/
$PROJECT_DIR/data/features_671.npy
$PROJECT_DIR/data/features_pca50.npy
```

正式跑法：

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

正式結果會存到：

```text
$PROJECT_DIR/outputs/formal_v1/
$PROJECT_DIR/outputs/formal_v1.zip
```

## 4. 如果不用 colab_runner.py，也可以手動跑

```bash
python build_items_from_dataset.py \
  --dataset-root "$PROJECT_DIR/data/interior-design-styles" \
  --output "$PROJECT_DIR/data/items.csv" \
  --class-counts-output "$PROJECT_DIR/data/class_counts.csv" \
  --dataset-summary-output "$PROJECT_DIR/data/dataset_summary.json"

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

## 5. 本機 / bash smoke test

```bash
pip install -r requirements.txt
./evaluate_pipeline.sh 50 100 outputs_smoke
```

## 6. Windows / PowerShell note

若 `evaluate_pipeline.sh` 在 PowerShell 無法直接執行，請改用手動指令：

```bash
python make_demo_items.py --output data/items.csv --n-items 3729 --n-styles 19 --seed 42
python run_pipeline.py --items data/items.csv --generate-mock-features --n-sessions 50 --steps-per-session 100 --output-dir outputs_smoke --skip-cosine-sim-save
```

## Models

- Random
- Popularity/PageRank
- Visual-only LinUCB
- PageRank-LinUCB
- SimGraph-LinUCB
- Bridge-LinUCB
- Full Graph-Enhanced LinUCB

## 主要輸出

### A. Recommendation Benchmark（主證據）
- `offline_performance_results.csv`
- `offline_performance_by_seed.csv`
- `offline_performance_summary.csv`（long format: model, metric, mean, std, n, ci95_low, ci95_high）
- `ablation_results.csv`
- `learning_curves.csv`

### B. Graph-prior / beyond-accuracy
- `beyond_accuracy_metrics.csv`
- `bridge_metrics.csv`
- `style_coverage_results.csv`（`exposure_style_coverage`, `early_exposure_style_coverage`）
- `graph_stats.csv`
- `graph_priors.csv`

### C. Runtime diagnostics（輔助）
- `benchmark_results.csv`（`model`, `seed`, `execution_time_sec`, `memory_mb`, `throughput_steps_per_sec`）

### D. Case analysis（敘事補充）
- `case_analysis_report.md`
- `recommendation_event_logs.csv`（含 `seed`, `session_id`, `within_session_step`, `global_step`）
- `output_manifest.json`（列出本次輸出檔與大小，方便確認 Colab/Drive 資產）

> 案例分析僅作為模型行為的描述性補充，不取代整體 benchmark 與 repeated-seed 統計結果。

## Colab 重開後要不要重跑？

- **Smoke test**：可以重跑。
- **Features / formal outputs**：不要每次重跑，請保存在 Google Drive。
- **論文畫圖與表格**：直接讀 `$PROJECT_DIR/outputs/formal_v1/*.csv`。
- 只有在 simulation logic、reward function、features、graph threshold、seeds 或 model list 改變時，才重跑 formal benchmark。
