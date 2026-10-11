# Rank Tracker

Manual DataForSEO rank tracking for **melbournelandscape.com.au** in Google Australia.

Each run finds all organic keywords ranking in Google's top 100 results and produces exactly these columns:

| Column | Meaning |
| --- | --- |
| `keyword` | Google search keyword |
| `ranking_position` | Current organic position in Google Australia |
| `monthly_search_volume` | DataForSEO monthly Australian search volume |

No CPC data is collected. There is no schedule—runs happen only when you start them.

## One-time setup

In this repository, open **Settings → Secrets and variables → Actions → New repository secret** and add:

- `DFS_LOGIN` — your DataForSEO API login
- `DFS_PASSWORD` — your DataForSEO API password

## Run it manually

1. Open the **Actions** tab.
2. Select **Rank Tracker**.
3. Click **Run workflow** → **Run workflow**.
4. When it finishes, open `results/latest_rankings.csv` in the repository.

A dated CSV is also saved in `results/`, and both files are available from the run's **australia-rankings** artifact.

## Change the domain later

Edit `TARGET_DOMAIN` in `.github/workflows/rank-tracker.yml`.
