# 重新建立 private repo（不要再用 public fork）

你現在的 `text-summarizer` 是從 public repo fork 出來的，所以 GitHub 會顯示 public fork。若你希望隱私，最穩的做法是：**建立一個全新的 private repo，不要 fork，且不要複製舊的 `.git/` 歷史。**

---

## 最推薦流程

### Step 1：產生乾淨資料夾

在目前 repo 執行：

```bash
./prepare_private_repo.sh ../interior-style-recommender-private
```

這會建立一個乾淨資料夾：

```text
../interior-style-recommender-private/
```

裡面只會放推薦系統需要的 `.py`、`.md`、`requirements.txt`，不會帶原本 fork 的 `.git`。

---

## Step 2：到 GitHub 建立 private repo

1. GitHub → New repository
2. Repository name 建議：

```text
interior-style-recommender
```

3. 選 **Private**
4. 不要選 Fork
5. 如果要直接 push 這個資料夾，建議不要先勾 README 初始化

---

## Step 3：把乾淨資料夾 push 到 private repo

```bash
cd ../interior-style-recommender-private
git init
git add .
git commit -m "Initial private recommendation benchmark pipeline"
git branch -M main
git remote add origin https://github.com/<你的帳號>/interior-style-recommender.git
git push -u origin main
```

---

## 為什麼不要直接把 fork 改 private？

因為 public repo 的 fork 通常不能直接改成 private；而且就算改 remote，舊 `.git` history 仍然帶有 fork 來源紀錄。正式論文專案建議用乾淨 private repo。

---

## 哪些東西不要放進 GitHub？

`prepare_private_repo.sh` 會自動建立 `.gitignore`，排除：

```text
data/
outputs/
*.npy
*.pkl
*.zip
__pycache__/
```

建議：

- Kaggle 圖片資料放 Google Drive，不要 push。
- `features_671.npy`、`features_pca50.npy` 放 Google Drive，不要 push。
- `outputs/formal_v1/` 放 Google Drive，不要 push。

---

## Colab 之後怎麼用 private repo？

如果 private repo 在 GitHub，你可以在 Colab 用 token clone：

```bash
cd /content
git clone https://<TOKEN>@github.com/<你的帳號>/interior-style-recommender.git
cd interior-style-recommender
pip install -r requirements.txt
```

更簡單也更安全的方式：把這個 private repo 資料夾下載成 ZIP，解壓後上傳到 Google Drive：

```text
MyDrive/thesis_recommender/
```

然後照 `COLAB_BLOCKS.md` 執行。
