# How to publish this repository

This folder is a **clean, self-contained** copy with no history from the
private bot repository and no secrets. Follow these steps to publish it.

## 1. Final secret scan (do this even though it was already scanned)

```bash
# Recommended: install gitleaks (https://github.com/gitleaks/gitleaks)
brew install gitleaks
gitleaks detect --source . --no-git -v

# Quick manual fallback:
grep -rinE "api[_-]?key|secret|password|token|BEGIN (RSA|EC|OPENSSH)" src tests docs paper
```

Expected: no findings. The datasets under `data/` are gitignored and contain
only public market data.

## 2. Initialize a fresh git repo (no private history)

```bash
cd chocotrader-research
git init
git add .
git status            # confirm: no .parquet, no .env, no .venv
git commit -m "Initial public release: simulators, datasets fetchers, and paper"
```

> Do **not** import history from the private repo (no `git filter-branch`,
> no `git subtree`). A fresh `git init` guarantees no secret ever existed in
> this repo's history.

## 3. Create the remote and push

```bash
# Create an empty public repo on GitHub named e.g. chocotrader-research, then:
git remote add origin git@github.com:<you>/chocotrader-research.git
git branch -M main
git push -u origin main
```

## 4. Verify reproducibility on a clean clone

```bash
git clone git@github.com:<you>/chocotrader-research.git /tmp/verify
cd /tmp/verify
make install
make fetch        # downloads data from Binance / alternative.me / FRED
make test         # 26 tests must pass
make reproduce    # regenerates the v6 tables; walk-forward must report
                  # "NO strategy passes W3 gate"
```

## 5. (Optional) Mint a DOI and a preprint

- Connect the GitHub repo to **Zenodo** and cut a release → Zenodo assigns a
  DOI automatically. Put the DOI in `CITATION.cff` and the README badge.
- For a preprint: **SSRN** (no endorsement needed) or **arXiv q-fin.TR**
  (needs endorsement). Convert the paper to PDF with:
  `pandoc paper/chocotrader-paper-en.md -o paper.pdf`

## What was deliberately excluded (and why)

- The production bot (`chocotrader/` adapters with live I/O), all infrastructure
  (`deploy/`, k8s, Jenkins), and every secret/credential. This repo is the
  *research*, not the trading system.
- The sealed out-of-sample dataset — never accessed, kept sealed.
- Raw market data — regenerable via the fetchers, not redistributed.
