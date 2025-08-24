# Price Finder / Product Price Tracker

A full‑stack web app to search products and visualize their price history across different periods (today, week, month, year). Includes on‑demand price refresh and store selection.

## Features
- Search products by name; auto‑create if not found
- View current price and interactive charts for Today/Week/Month/Year
- Single‑product "Refresh Price" action
- Store selection (e.g., Amazon, Apple, Best Buy, Walmart, Target, Samsung, Olive Young)
- Search history with quick switching

## Tech Stack
- Frontend
  - React + TypeScript
  - Vite
  - Tailwind CSS + shadcn/ui components
  - Recharts (charts)
  - lucide-react (icons)
- Backend
  - Python (3.9+)
  - Flask
  - SQLAlchemy + SQLite
  - Flask-CORS
- Deployment
  - Vercel (Frontend static hosting + Python Serverless Functions)
  - Root config: `vercel.json`
  - API entrypoint: `api/index.py` (imports Flask app from `server/index.py`)

## Repository structure
```
/price_tracker
  /backend
    app/                # Flask app package (routes, models, services)
    instance/           # SQLite DB location
    requirements.txt
    wsgi.py             # Local dev entrypoint (port 3001)
  /frontend
    src/                # React + TS source
    public/
    index.html
    package.json
/server
  index.py              # Creates Flask app via app factory
  requirements.txt
  server.py             # (optional local runner)
/api
  index.py              # Vercel Serverless Function shim to import server/index.py
  requirements.txt      # Refs ../server/requirements.txt
vercel.json             # Build + rewrites config
```

## Local development
Prereqs: Python 3.9+, Node 18+

1) Backend
```
cd price_tracker/backend
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
python wsgi.py                 # Runs http://127.0.0.1:3001
```

2) Frontend
```
cd price_tracker/frontend
npm install
npm run dev                    # Runs http://127.0.0.1:5173
```
The frontend will call the backend at `http://localhost:3001` in development (see `API_BASE_URL` in `src/screens/LightCover/LightCover.tsx`).

## Key API endpoints
Base URL: `/api`
- GET `/api/healthcheck`
- GET `/api/products`
- POST `/api/products` body: `{ name: string, store?: string }`
- GET `/api/products/by-name?name=...`
- GET `/api/products/:id/price_history`
- GET `/api/products/:id/price_average?period=today|week|month|year`
- POST `/api/products/:id/refresh` body: `{ store?: string }`

## Data and price generation
- When creating a product, the backend seeds historical data for today/week/month/year for charting.
- Historical generation uses a depreciation‑aware model (earlier prices tend to be higher than today with mild noise and clamping) for more realistic trends.
- The Refresh action attempts a store‑specific scrape/fetch and appends a new point to history.

## Deployment (Vercel)
- Root config: `vercel.json`
  - Builds frontend: `cd price_tracker/frontend && npm install && npm run build`
  - Serves static output from `price_tracker/frontend/dist`
  - Rewrites `/api/*` to `api/index.py`
- Serverless function:
  - `api/index.py` ensures `server/` is on `PYTHONPATH` and imports `app` from `server/index.py`
  - `api/requirements.txt` references `../server/requirements.txt` to install Python deps

Typical steps:
1. Connect the GitHub repo to Vercel.
2. Use the repo defaults; Vercel will run the build command from `vercel.json`.
3. After deploy:
   - Frontend: `https://<project>.vercel.app/`
   - API: `https://<project>.vercel.app/api/healthcheck`

## Notes
- SQLite is great for demos; switch to a hosted DB for production.
- Be respectful of target sites’ ToS if enabling scraping.
- Env vars can be configured in Vercel dashboard if needed.
