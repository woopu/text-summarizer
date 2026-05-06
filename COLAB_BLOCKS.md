# Colab 貼上用分段區塊

> 使用方式：在 Google Colab 依序新增 cell，照下面「Block 0, Block 1, ...」一格一格貼上執行。  
> Smoke test 可以先跑；正式論文結果請跑 Formal blocks。

---

## Block 0：掛載 Google Drive（Python cell）

```python
from google.colab import drive
drive.mount('/content/drive')
```

---

## Block 1：設定 repo / project 路徑（Bash cell）

> 假設你已經把本 repo 放在 Google Drive 的 `MyDrive/thesis_recommender`。  
> 如果你的資料夾名稱不同，只改 `PROJECT_DIR=...` 這一行。

```bash
%%bash
PROJECT_DIR=/content/drive/MyDrive/thesis_recommender
cd "$PROJECT_DIR"
pwd
mkdir -p "$PROJECT_DIR/data" "$PROJECT_DIR/outputs"
```

---

## Block 2：安裝套件（Bash cell）

```bash
%%bash
PROJECT_DIR=/content/drive/MyDrive/thesis_recommender
cd "$PROJECT_DIR"
pip install -r requirements.txt
```

---

## Block 3：先跑 smoke test（Bash cell）

> 目的：確認 pipeline 能跑、輸出檔能寫到 Drive。  
> 注意：這是 mock features，不可當正式論文結果。

```bash
%%bash
PROJECT_DIR=/content/drive/MyDrive/thesis_recommender
cd "$PROJECT_DIR"
python colab_runner.py \
  --project-dir "$PROJECT_DIR" \
  --mode smoke \
  --n-sessions 50 \
  --steps-per-session 100 \
  --output-name smoke \
  --skip-cosine-sim-save \
  --compress-output
```

---

## Block 4：檢查 smoke test 輸出（Python cell）

```python
from pathlib import Path
import pandas as pd

PROJECT_DIR = Path('/content/drive/MyDrive/thesis_recommender')
out = PROJECT_DIR / 'outputs' / 'smoke'
print('Output folder:', out)
print('Exists:', out.exists())
print('\nFiles:')
for p in sorted(out.glob('*')):
    print('-', p.name)

perf_path = out / 'offline_performance_results.csv'
if perf_path.exists():
    display(pd.read_csv(perf_path))
```

---

## Block 5：確認正式資料與 feature 檔位置（Python cell）

> 正式跑之前，請確認 Drive 裡有：
>
> - `data/interior-design-styles/`
> - `data/features_671.npy`
> - `data/features_pca50.npy`

```python
from pathlib import Path

PROJECT_DIR = Path('/content/drive/MyDrive/thesis_recommender')
checks = [
    PROJECT_DIR / 'data' / 'interior-design-styles',
    PROJECT_DIR / 'data' / 'features_671.npy',
    PROJECT_DIR / 'data' / 'features_pca50.npy',
]

for path in checks:
    print(path, '✅ exists' if path.exists() else '❌ missing')
```

---

## Block 6：建立正式 items.csv / class_counts / dataset_summary（Bash cell）

```bash
%%bash
PROJECT_DIR=/content/drive/MyDrive/thesis_recommender
cd "$PROJECT_DIR"
python build_items_from_dataset.py \
  --dataset-root "$PROJECT_DIR/data/interior-design-styles" \
  --output "$PROJECT_DIR/data/items.csv" \
  --class-counts-output "$PROJECT_DIR/data/class_counts.csv" \
  --dataset-summary-output "$PROJECT_DIR/data/dataset_summary.json"
```

---

## Block 7：正式 repeated-seed benchmark（Bash cell）

> 這一步會花比較久。正式結果會存到 Drive：  
> `$PROJECT_DIR/outputs/formal_v1/` 與 `$PROJECT_DIR/outputs/formal_v1.zip`

```bash
%%bash
PROJECT_DIR=/content/drive/MyDrive/thesis_recommender
cd "$PROJECT_DIR"
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

---

## Block 8：檢查正式輸出與主要結果表（Python cell）

```python
from pathlib import Path
import pandas as pd

PROJECT_DIR = Path('/content/drive/MyDrive/thesis_recommender')
out = PROJECT_DIR / 'outputs' / 'formal_v1'
print('Output folder:', out)
print('Zip:', Path(str(out) + '.zip'), Path(str(out) + '.zip').exists())

expected = [
    'config.json',
    'offline_performance_results.csv',
    'offline_performance_by_seed.csv',
    'offline_performance_summary.csv',
    'ablation_results.csv',
    'learning_curves.csv',
    'beyond_accuracy_metrics.csv',
    'bridge_metrics.csv',
    'style_coverage_results.csv',
    'graph_stats.csv',
    'graph_priors.csv',
    'benchmark_results.csv',
    'case_analysis_report.md',
    'recommendation_event_logs.csv',
    'output_manifest.json',
]

for name in expected:
    print(f'{name}:', '✅' if (out / name).exists() else '❌')

print('\nPerformance summary:')
display(pd.read_csv(out / 'offline_performance_summary.csv'))
```

---

## Block 9：之後 Colab 重開，只讀結果不用重跑（Python cell）

```python
from pathlib import Path
import pandas as pd

PROJECT_DIR = Path('/content/drive/MyDrive/thesis_recommender')
out = PROJECT_DIR / 'outputs' / 'formal_v1'

perf = pd.read_csv(out / 'offline_performance_summary.csv')
curves = pd.read_csv(out / 'learning_curves.csv')
bridge = pd.read_csv(out / 'bridge_metrics.csv')

print('Loaded previous formal results from:', out)
display(perf.head())
display(bridge.head())
```

---

## 最重要提醒

- Block 3 是 smoke test：可以重跑。
- Block 7 是正式實驗：不要每次 Colab 重開都重跑。
- Colab 重開後通常只需要跑 Block 0、Block 1、Block 2，然後用 Block 9 讀舊結果。
- `--skip-cosine-sim-save` 只是不把 `cosine_sim.npy` 寫到 Drive；similarity matrix 仍會在記憶體中計算。
