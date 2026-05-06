#!/usr/bin/env bash
set -euo pipefail

DEST=${1:-../interior-style-recommender-private}

FILES=(
  README.md
  COLAB_BLOCKS.md
  COLAB_UPLOAD_GUIDE.md
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
)

mkdir -p "$DEST"
for file in "${FILES[@]}"; do
  cp "$file" "$DEST/"
done

cat > "$DEST/.gitignore" <<'EOF'
__pycache__/
*.py[cod]
.ipynb_checkpoints/
.DS_Store
.env
.venv/
venv/
data/
outputs/
outputs_*/
*.zip
*.npy
*.pkl
*.joblib
EOF

cat > "$DEST/README_PRIVATE_SETUP.md" <<'EOF'
# Private repo setup

This folder is a clean copy of the recommendation benchmark pipeline without the original fork's `.git` history.

## Create a new private GitHub repo

1. Go to GitHub → New repository.
2. Repository name suggestion: `interior-style-recommender`.
3. Select **Private**.
4. Do not create it as a fork.
5. Do not initialize with README if you plan to push this folder directly.

## Push this clean folder

```bash
cd <this-folder>
git init
git add .
git commit -m "Initial private recommendation benchmark pipeline"
git branch -M main
git remote add origin https://github.com/<YOUR_ACCOUNT>/interior-style-recommender.git
git push -u origin main
```

## Important

- Do not copy the old `.git/` directory from the public fork.
- Keep `data/`, `outputs/`, `.npy`, `.pkl`, and zip artifacts out of Git.
- Store large/private assets in Google Drive or another private storage location.
EOF

echo "Clean private-repo folder prepared at: $DEST"
echo "Next: create a NEW PRIVATE GitHub repo (not a fork), then push from $DEST."
