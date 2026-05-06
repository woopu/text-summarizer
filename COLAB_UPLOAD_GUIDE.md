# 怎麼把這些 `.py` 檔案給 Colab 跑？

你有三種方式。**最推薦方式 A：把整個 repo 資料夾放到 Google Drive**，因為正式實驗輸出也要存 Drive，Colab 重開後比較不會遺失。

---

## 方式 A（最推薦）：整個 repo 資料夾放到 Google Drive

### A1. 在你的電腦準備資料夾

把整個專案資料夾整理成：

```text
thesis_recommender/
  README.md
  COLAB_BLOCKS.md
  PY_FILES_GUIDE.md
  requirements.txt
  colab_runner.py
  run_pipeline.py
  simulation.py
  metrics.py
  benchmark.py
  build_items_from_dataset.py
  make_demo_items.py
  recommender_pipeline.py
  evaluate_pipeline.sh
  data/
  outputs/
```

至少要有這些 `.py`：

```text
colab_runner.py
run_pipeline.py
simulation.py
metrics.py
benchmark.py
build_items_from_dataset.py
make_demo_items.py
recommender_pipeline.py
```

### A2. 上傳到 Google Drive

把整個 `thesis_recommender/` 資料夾上傳到：

```text
Google Drive / MyDrive / thesis_recommender
```

### A3. Colab 第一格：掛載 Drive

```python
from google.colab import drive
drive.mount('/content/drive')
```

### A4. Colab 第二格：切到 repo 資料夾並安裝套件

```bash
%%bash
PROJECT_DIR=/content/drive/MyDrive/thesis_recommender
cd "$PROJECT_DIR"
pwd
pip install -r requirements.txt
mkdir -p "$PROJECT_DIR/data" "$PROJECT_DIR/outputs"
```

### A5. Colab 第三格：跑 smoke test

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

### A6. Colab 第四格：檢查輸出

```python
from pathlib import Path
import pandas as pd

PROJECT_DIR = Path('/content/drive/MyDrive/thesis_recommender')
out = PROJECT_DIR / 'outputs' / 'smoke'
print(out)
for p in sorted(out.glob('*')):
    print(p.name)

display(pd.read_csv(out / 'offline_performance_results.csv'))
```

---

## 方式 B：用 GitHub clone 到 Colab

如果你把 repo 放到 GitHub，可以在 Colab 直接 clone：

```bash
%%bash
cd /content
git clone <你的 GitHub repo URL> thesis_recommender
cd /content/thesis_recommender
pip install -r requirements.txt
```

然後 smoke test：

```bash
%%bash
PROJECT_DIR=/content/drive/MyDrive/thesis_recommender_outputs
mkdir -p "$PROJECT_DIR/data" "$PROJECT_DIR/outputs"
cd /content/thesis_recommender
python colab_runner.py \
  --project-dir "$PROJECT_DIR" \
  --mode smoke \
  --n-sessions 50 \
  --steps-per-session 100 \
  --output-name smoke \
  --skip-cosine-sim-save \
  --compress-output
```

> 這種方式下，repo 在 `/content/thesis_recommender`，輸出存在 Drive 的 `$PROJECT_DIR`。Colab 重開後 repo 可能要重新 clone，但 outputs 還在 Drive。

---

## 方式 C：只上傳 `.py` 檔到 Colab 左側 Files（不推薦正式實驗）

Colab 左側 Files 可以直接 upload `.py`，但 runtime 重開後可能消失，所以只適合短暫 debug。

你至少要上傳：

```text
requirements.txt
colab_runner.py
run_pipeline.py
simulation.py
metrics.py
benchmark.py
build_items_from_dataset.py
make_demo_items.py
recommender_pipeline.py
```

然後在 Colab：

```bash
%%bash
cd /content
pip install -r requirements.txt
python make_demo_items.py --output data/items.csv --n-items 3729 --n-styles 19 --seed 42
python run_pipeline.py \
  --items data/items.csv \
  --generate-mock-features \
  --n-sessions 50 \
  --steps-per-session 100 \
  --output-dir outputs_smoke \
  --skip-cosine-sim-save
```

> 不推薦用這個跑正式論文結果，因為 `/content` 會隨 Colab runtime 重開而消失。

---

## 正式資料要放哪裡？

如果用方式 A，請把資料放成：

```text
/content/drive/MyDrive/thesis_recommender/data/interior-design-styles/
/content/drive/MyDrive/thesis_recommender/data/features_671.npy
/content/drive/MyDrive/thesis_recommender/data/features_pca50.npy
```

正式跑：

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

## 最簡單記法

你在 Colab 主要只要記得：

```text
1. 整個 repo 放到 Drive 的 thesis_recommender/
2. Colab mount Drive
3. cd /content/drive/MyDrive/thesis_recommender
4. pip install -r requirements.txt
5. python colab_runner.py --mode smoke ...
6. 正式資料/features 放好後 python colab_runner.py --mode formal ...
```

`.py` 不需要一個一個貼進 notebook；**把 `.py` 當成檔案放進 Drive/repo，Colab cell 只負責用 `python xxx.py ...` 執行它。**
