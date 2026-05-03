# GreenRoute India

Eco-friendly travel planner for synthetic Indian routes. The frontend is React and the backend is a small Python standard-library API that stores trip history and reward points in SQLite.

## Run

Install frontend dependencies:

```bash
npm install
```

Install backend dependencies:

```bash
pip install -r requirements.txt
```

Start the FastAPI backend:

```bash
python -m uvicorn backend.server:app --host 127.0.0.1 --port 8000
```

If PowerShell blocks `npm`, use `npm.cmd install` and `npm.cmd run dev`.

Start the React app:

```bash
npm run dev
```

Open the Vite URL shown in the terminal. The frontend expects the API at `http://127.0.0.1:8000`.

## Features

- Synthetic India places and approximate map coordinates.
- Eco, balanced, and fast route recommendations with route scoring.
- Multi-modal route segments including walking, cycling, metro, bus, train, EV, car, and flight.
- CO2 calculation by segment using passenger count, luggage, regional grid intensity, congestion, and g/passenger-km factors.
- Reward points for saved lower-emission trips.
- Leaflet maps for each route, plus a dedicated maps comparison tab.
- Recharts route comparison for CO2, baseline, and duration.
- SQLite-backed travel history through a lightweight Python backend.
