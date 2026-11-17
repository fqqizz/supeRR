# SupeRR Analytics | Pressure Lab

**SupeRR Selector Season 2 · Round 1**  
Prepared by Faaiz Qureshi · 17 November 2026

A deployable, responsive, monochrome research dashboard for the Round 1 question: identify the top ten batters and top ten bowlers who perform best under pressure. It documents the pressure definition, exposes player-level evidence, and lets a reviewer explore alternative scoring weights. It does **not** make auction retention or acquisition recommendations.

## Start locally (Windows)

1. Extract the ZIP file.
2. Install **Node.js 18 or newer** from https://nodejs.org/ if it is not already installed.
3. Double-click `run-local.bat`.
4. Open `http://localhost:3000` if the browser does not open automatically.

On macOS/Linux, run `./run-local.sh` from the project folder. Or run `node server.js` directly.

The runtime dashboard has no npm package dependencies and does not require a database, API key, account or external service. The local Node server serves the dashboard and the same analytics API used by the Vercel deployment.

## Deploy to Vercel

1. Extract this project and push the **contents of this folder** to a GitHub repository.
2. In Vercel, import that repository.
3. Select **Other** as the framework preset.
4. Leave the build command and output-directory override empty. No frontend build step is required.
5. Deploy. Vercel serves the files in `public/` and deploys `api/analytics.js` as a Node serverless function.

The Vercel project root must contain `api/`, `public/`, `package.json` and `vercel.json`. Do not set the project root to the `public` folder.

## Design and navigation

The interface uses a white background, black and grey text, restrained rules, a serif display/body treatment and plain sans-serif controls. Decorative gradients, colourful cards and promotional headlines have been removed. The layout is designed to read like a research workspace rather than a marketing landing page.

## What is included

- **Overview:** dataset scope, pressure-event counts and official top performers.
- **Batting index:** final combined ranking plus IPL-only and T20I-only balanced reference rankings.
- **Bowling index:** final combined ranking plus IPL-only and T20I-only balanced reference rankings.
- **Player profiles:** search a player to view available IPL and T20I records, pressure/death exposure, rates, evidence support, confidence intervals, role coverage and component scores. Missing format data means the player has no qualifying record in that format.
- **Scenario testing:** choose batting or bowling, choose combined/IPL/T20I scope, select a format blend where relevant, set component weights and recalculate. The API normalises non-negative weights to 100%, calculates a custom composite from precomputed adjusted component scores and sorts the eligible players. This output is not the official list and does not overwrite it.
- **Methodology:** embedded method summary, standalone HTML report and nine-page PDF report.
- **Evidence files:** compact JSON data used by the dashboard, alongside the original organiser data pack, filtered delivery-state file and precomputed scoring tables.
- **Journey reel script:** optional 25-35 second video outline and caption in `docs/journey-reel-script.md`.

## Architecture

```text
Browser
  └── public/index.html + styles.css + app.js
        └── /api/analytics?action=...
              └── api/analytics.js
                    └── public/data/*.json

Local development:
  node server.js  -> static file server + same analytics handler

Vercel:
  public/            -> static web assets
  api/analytics.js   -> serverless Node API
```

The player tables and rankings are read from the validated JSON exports in `public/data`. The scenario studio performs weighted score calculations in the API using the already-normalised dimension components. The browser does not need to download or process the full delivery file to render a player profile.

## Data and scope

The primary ranking scope is **IPL 2022-2026 and T20I only**. Other domestic T20 competitions in the organiser pack are excluded from the primary comparison. The final filtered dataset contains 828 matches (364 IPL and 464 T20I), 193,372 primary-eligible delivery rows and 57,330 pressure-union deliveries.

The core batting pressure definition is:

> Death phase (at least 75% of scheduled legal balls completed) **OR** at least five wickets already lost before the delivery.

The bowler index evaluates death-phase bowling. All labels use pre-delivery state to avoid look-ahead leakage. Full formulas, peer groups, minimum samples, scenario weights, final results and limitations are in `public/reports/SupeRR_Pressure_Methodology_Report.pdf` and `public/methodology.html`.

## Rebuild the dashboard data locally

The web app runs without Python. Python is only required when you want to regenerate the compact JSON exports or PDF from the bundled intermediate data.

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python scripts/build_app_data.py
python scripts/create_methodology_report.py
```

The export script reads the bundled `research-data/processed/` scorecards and evidence tables. It does not depend on `/mnt/data` or an external path. The organiser's original data pack and filtered delivery-state file are retained in `research-data/` for provenance and further research.

## API endpoints

All endpoints are served through `/api/analytics`:

| Action | Parameters | Purpose |
|---|---|---|
| `overview` | none | Dataset and validation metadata |
| `rankings` | `type=batting\|bowling`, `format=combined\|IPL\|T20I`, `limit=10` | Official or format-specific rankings |
| `player` | `type`, `name` | Player profile across available formats |
| `players` | `type`, optional `q`, `format`, `eligible=true` | Search the player-format pool |
| `scenarios` | `type` | All precomputed sensitivity scenarios |
| `custom-rankings` | `type`, `format`, weights and blend | Recalculate a custom ranking |

Example:

```text
/api/analytics?action=rankings&type=batting&format=combined&limit=10
/api/analytics?action=custom-rankings&type=bowling&format=combined&blend=ipl70&effectiveness=65&consistency=35
```

## Interpretation notes

- Combined official rankings are ordered by mean rank across five batting weighting configurations × three format blends (15 scenarios), and three bowling configurations × three blends (9 scenarios).
- Top-ten stability is the proportion of tested scenarios in which a player remained in the top ten. It is not a probability of future performance.
- Format percentiles are relative peer positions, not probabilities.
- Known bowling boundary events are a partial proxy. The supplied data does not support an official economy or complete dot-ball rate.
- Exact required run rate and score margin are not reconstructed from the supplied extras fields.
- Historical pressure performance is not current player availability or a franchise recommendation.

## Project verification

Run:

```bash
node --check api/analytics.js
node --check server.js
node --check public/app.js
python scripts/validate_project.py
```

A successful validation prints `PASS` for the data schemas, top-ten outputs, score bounds, cross-format candidate counts and API-compatible metadata.
"# supeRR" 
