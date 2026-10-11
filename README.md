# Rank Tracker

Manual DataForSEO rank tracking for **melbournelandscape.com.au** in Google **Melbourne, Victoria**.

The tracker first finds the domain's existing Google Australia keywords, then checks each keyword in a live Google result set located in Melbourne. The CSV contains exactly:

| Column | Meaning |
| --- | --- |
| `keyword` | Google search keyword |
| `ranking_position` | Current organic position in Google Melbourne |
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
4. When it finishes, open `results/melbourne_rankings.csv` in the repository.

Only one CSV is produced and downloaded per run. The same file is replaced with fresh results each time, and it is also available from the run's **melbourne-rankings** artifact.

Because it performs a live Melbourne Google check for each discovered keyword, a run uses DataForSEO SERP API credits. Results include only keywords where the website is in Google's top 100 Melbourne organic results.
