# Rank Tracker

Manual DataForSEO rank tracking for **melbournelandscape.com.au** in Google **Melbourne, Victoria**.

Each run finds all organic keywords ranking in Google's top 100 results when searched from Melbourne and produces exactly these columns:

| Column | Meaning |
| --- | --- |
| `keyword` | Google search keyword |
| `ranking_position` | Current organic position in Google Melbourne |
| `monthly_search_volume` | DataForSEO monthly search volume for Melbourne |

No CPC data is collected. There is no schedule—runs happen only when you start them.

## One-time setup

In this repository, open **Settings → Secrets and variables → Actions → New repository secret** and add:

- `DFS_LOGIN` — your DataForSEO API login
- `DFS_PASSWORD` — your DataForSEO API password

## Run it manually

1. Open the **Actions** tab.
2. Select **Rank Tracker**.
3. Click **Run workflow** → **Run workflow**.
4. When it finishes, open `results/melbourne_rankings.csv` in the repository.

Only one CSV is produced and downloaded per run. The same file is replaced with fresh results each time, and it is also available from the run's **melbourne-rankings** artifact.

## Change the domain or location later

Edit `TARGET_DOMAIN` or `LOCATION_NAME` in `.github/workflows/rank-tracker.yml`.
