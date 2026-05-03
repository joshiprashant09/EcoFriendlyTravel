from datetime import datetime, timezone
from enum import Enum
import math
import os
import sqlite3
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "travel_history.db")
HOST = "127.0.0.1"
PORT = int(os.environ.get("GREENROUTE_PORT", "8000"))


class Preference(str, Enum):
    eco = "eco"
    balanced = "balanced"
    fast = "fast"


class SaveTripRequest(BaseModel):
    fromId: str
    toId: str
    routeId: str
    passengers: int = 1
    luggageKg: float = 8


PLACES = [
    {"id": "delhi", "name": "Delhi", "state": "Delhi", "lat": 28.6139, "lng": 77.2090, "region": "north", "transit": 91},
    {"id": "new-delhi-station", "name": "New Delhi Railway Station", "state": "Delhi", "lat": 28.6431, "lng": 77.2197, "region": "north", "transit": 96},
    {"id": "mumbai", "name": "Mumbai", "state": "Maharashtra", "lat": 19.0760, "lng": 72.8777, "region": "west", "transit": 94},
    {"id": "bengaluru", "name": "Bengaluru", "state": "Karnataka", "lat": 12.9716, "lng": 77.5946, "region": "south", "transit": 82},
    {"id": "chennai", "name": "Chennai", "state": "Tamil Nadu", "lat": 13.0827, "lng": 80.2707, "region": "south", "transit": 86},
    {"id": "kolkata", "name": "Kolkata", "state": "West Bengal", "lat": 22.5726, "lng": 88.3639, "region": "east", "transit": 89},
    {"id": "hyderabad", "name": "Hyderabad", "state": "Telangana", "lat": 17.3850, "lng": 78.4867, "region": "south", "transit": 80},
    {"id": "pune", "name": "Pune", "state": "Maharashtra", "lat": 18.5204, "lng": 73.8567, "region": "west", "transit": 75},
    {"id": "ahmedabad", "name": "Ahmedabad", "state": "Gujarat", "lat": 23.0225, "lng": 72.5714, "region": "west", "transit": 77},
    {"id": "jaipur", "name": "Jaipur", "state": "Rajasthan", "lat": 26.9124, "lng": 75.7873, "region": "north", "transit": 69},
    {"id": "lucknow", "name": "Lucknow", "state": "Uttar Pradesh", "lat": 26.8467, "lng": 80.9462, "region": "north", "transit": 72},
    {"id": "varanasi", "name": "Varanasi", "state": "Uttar Pradesh", "lat": 25.3176, "lng": 82.9739, "region": "north", "transit": 62},
    {"id": "goa", "name": "Panaji, Goa", "state": "Goa", "lat": 15.4909, "lng": 73.8278, "region": "west", "transit": 58},
    {"id": "kochi", "name": "Kochi", "state": "Kerala", "lat": 9.9312, "lng": 76.2673, "region": "south", "transit": 79},
    {"id": "thiruvananthapuram", "name": "Thiruvananthapuram", "state": "Kerala", "lat": 8.5241, "lng": 76.9366, "region": "south", "transit": 74},
    {"id": "mysuru", "name": "Mysuru", "state": "Karnataka", "lat": 12.2958, "lng": 76.6394, "region": "south", "transit": 68},
    {"id": "ooty", "name": "Ooty", "state": "Tamil Nadu", "lat": 11.4064, "lng": 76.6932, "region": "south", "transit": 46},
    {"id": "udaipur", "name": "Udaipur", "state": "Rajasthan", "lat": 24.5854, "lng": 73.7125, "region": "north", "transit": 52},
    {"id": "amritsar", "name": "Amritsar", "state": "Punjab", "lat": 31.6340, "lng": 74.8723, "region": "north", "transit": 63},
    {"id": "chandigarh", "name": "Chandigarh", "state": "Chandigarh", "lat": 30.7333, "lng": 76.7794, "region": "north", "transit": 71},
    {"id": "shimla", "name": "Shimla", "state": "Himachal Pradesh", "lat": 31.1048, "lng": 77.1734, "region": "north", "transit": 48},
    {"id": "rishikesh", "name": "Rishikesh", "state": "Uttarakhand", "lat": 30.0869, "lng": 78.2676, "region": "north", "transit": 50},
    {"id": "bhopal", "name": "Bhopal", "state": "Madhya Pradesh", "lat": 23.2599, "lng": 77.4126, "region": "central", "transit": 66},
    {"id": "indore", "name": "Indore", "state": "Madhya Pradesh", "lat": 22.7196, "lng": 75.8577, "region": "central", "transit": 69},
    {"id": "nagpur", "name": "Nagpur", "state": "Maharashtra", "lat": 21.1458, "lng": 79.0882, "region": "central", "transit": 73},
    {"id": "bhubaneswar", "name": "Bhubaneswar", "state": "Odisha", "lat": 20.2961, "lng": 85.8245, "region": "east", "transit": 67},
    {"id": "guwahati", "name": "Guwahati", "state": "Assam", "lat": 26.1445, "lng": 91.7362, "region": "east", "transit": 59},
    {"id": "patna", "name": "Patna", "state": "Bihar", "lat": 25.5941, "lng": 85.1376, "region": "east", "transit": 61},
    {"id": "agra", "name": "Agra", "state": "Uttar Pradesh", "lat": 27.1767, "lng": 78.0081, "region": "north", "transit": 70},
    {"id": "noida", "name": "Noida", "state": "Uttar Pradesh", "lat": 28.5355, "lng": 77.3910, "region": "north", "transit": 85},
]

MODE_FACTORS = {
    "walk": {"label": "Walk", "g_per_passenger_km": 0, "speed_kmph": 4, "occupancy": 1, "reliability": 92},
    "cycle": {"label": "Cycle", "g_per_passenger_km": 0, "speed_kmph": 13, "occupancy": 1, "reliability": 86},
    "metro": {"label": "Metro", "g_per_passenger_km": 26, "speed_kmph": 34, "occupancy": 310, "reliability": 90},
    "bus": {"label": "Bus", "g_per_passenger_km": 62, "speed_kmph": 31, "occupancy": 42, "reliability": 72},
    "train": {"label": "Train", "g_per_passenger_km": 38, "speed_kmph": 68, "occupancy": 720, "reliability": 82},
    "ev": {"label": "Shared EV", "g_per_passenger_km": 74, "speed_kmph": 42, "occupancy": 3, "reliability": 78},
    "car": {"label": "Car", "g_per_passenger_km": 178, "speed_kmph": 54, "occupancy": 1.7, "reliability": 69},
    "flight": {"label": "Flight", "g_per_passenger_km": 246, "speed_kmph": 540, "occupancy": 168, "reliability": 76},
}

REGION_GRID_INTENSITY = {
    "north": 1.04,
    "south": 0.92,
    "west": 0.96,
    "east": 1.08,
    "central": 1.0,
}


def init_db() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS trips (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                route_id TEXT NOT NULL,
                preference TEXT NOT NULL,
                from_name TEXT NOT NULL,
                to_name TEXT NOT NULL,
                distance_km REAL NOT NULL,
                duration_min INTEGER NOT NULL,
                co2_kg REAL NOT NULL,
                reward_points INTEGER NOT NULL
            )
            """
        )


def place_by_id(place_id: str) -> dict[str, Any] | None:
    return next((place for place in PLACES if place["id"] == place_id), None)


def haversine_km(a: dict[str, Any], b: dict[str, Any]) -> float:
    radius = 6371
    lat1, lon1, lat2, lon2 = map(math.radians, [a["lat"], a["lng"], b["lat"], b["lng"]])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    x = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return radius * 2 * math.atan2(math.sqrt(x), math.sqrt(1 - x))


def distance_profile(a: dict[str, Any], b: dict[str, Any]) -> dict[str, float]:
    direct = haversine_km(a, b)
    road_factor = 1.16 if direct < 500 else 1.22
    rail_factor = 1.08 if direct < 500 else 1.12
    air_factor = 1.03
    return {
        "direct": round(direct, 1),
        "road": round(direct * road_factor, 1),
        "rail": round(direct * rail_factor, 1),
        "air": round(direct * air_factor, 1),
    }


def interpolate_points(a: dict[str, Any], b: dict[str, Any], bends: int, offset: float) -> list[dict[str, float]]:
    points = []
    for index in range(bends + 2):
        t = index / (bends + 1)
        curve = math.sin(math.pi * t) * offset
        points.append({
            "lat": round(a["lat"] + (b["lat"] - a["lat"]) * t + curve, 5),
            "lng": round(a["lng"] + (b["lng"] - a["lng"]) * t - curve * 0.55, 5),
        })
    return points


def route_blueprint(preference: Preference, distance: dict[str, float]) -> list[tuple[str, float, str]]:
    long_haul = distance["direct"] > 650
    short_city = distance["direct"] < 65
    if preference == Preference.eco:
        trunk = "metro" if short_city else "train"
        return [
            ("walk", 0.03, "Origin walk access"),
            ("cycle" if short_city else "bus", 0.09, "Low-emission feeder"),
            (trunk, 0.78, "Electric mass-transit trunk"),
            ("bus", 0.07, "Public last-mile connector"),
            ("walk", 0.03, "Destination walk access"),
        ]
    if preference == Preference.fast:
        if long_haul:
            return [
                ("ev", 0.07, "Airport electric connector"),
                ("flight", 0.86, "Fast domestic trunk"),
                ("ev", 0.07, "Destination airport connector"),
            ]
        return [
            ("car", 0.62, "Direct express road"),
            ("metro" if short_city else "train", 0.26, "Time-saving trunk"),
            ("ev", 0.12, "Shared electric final leg"),
        ]
    return [
        ("metro" if short_city else "train", 0.58, "Balanced trunk service"),
        ("bus", 0.24, "City-to-hub bus leg"),
        ("ev", 0.14, "Shared electric last mile"),
        ("walk", 0.04, "Short final walk"),
    ]


def segment_distance(mode: str, share: float, distances: dict[str, float]) -> float:
    if mode == "flight":
        base = distances["air"]
    elif mode in {"train", "metro"}:
        base = distances["rail"]
    else:
        base = distances["road"]
    return round(base * share, 1)


def calculate_segment(
    mode: str,
    share: float,
    label: str,
    a: dict[str, Any],
    b: dict[str, Any],
    distances: dict[str, float],
    passengers: int,
    luggage_kg: float,
    leg_index: int,
    total_legs: int,
) -> dict[str, Any]:
    factors = MODE_FACTORS[mode]
    km = segment_distance(mode, share, distances)
    grid_multiplier = (REGION_GRID_INTENSITY[a["region"]] + REGION_GRID_INTENSITY[b["region"]]) / 2
    congestion_multiplier = 1 + ((200 - a["transit"] - b["transit"]) / 1000)
    luggage_multiplier = 1 + min(luggage_kg, 40) * (0.002 if mode in {"flight", "car", "ev"} else 0.0008)
    mode_multiplier = grid_multiplier if mode in {"metro", "train", "ev"} else congestion_multiplier
    grams = km * factors["g_per_passenger_km"] * mode_multiplier * luggage_multiplier * passengers
    transfer_penalty = 4 if mode in {"metro", "train"} else 7 if mode == "bus" else 3
    duration = max(2, round((km / factors["speed_kmph"]) * 60 + transfer_penalty))
    from_step = a["name"] if leg_index == 0 else f"Interchange {leg_index}"
    to_step = b["name"] if leg_index == total_legs - 1 else f"Interchange {leg_index + 1}"
    return {
        "mode": mode,
        "label": factors["label"],
        "description": label,
        "from": from_step,
        "to": to_step,
        "distanceKm": km,
        "durationMin": duration,
        "co2Kg": round(grams / 1000, 2),
        "gPerPassengerKm": factors["g_per_passenger_km"],
        "occupancy": factors["occupancy"],
        "reliability": factors["reliability"],
    }


def route_payload(
    preference: Preference,
    a: dict[str, Any],
    b: dict[str, Any],
    distances: dict[str, float],
    passengers: int,
    luggage_kg: float,
) -> dict[str, Any]:
    blueprint = route_blueprint(preference, distances)
    segments = [
        calculate_segment(mode, share, label, a, b, distances, passengers, luggage_kg, index, len(blueprint))
        for index, (mode, share, label) in enumerate(blueprint)
    ]
    distance_km = round(sum(segment["distanceKm"] for segment in segments), 1)
    co2_kg = round(sum(segment["co2Kg"] for segment in segments), 2)
    duration = sum(segment["durationMin"] for segment in segments)
    car_baseline = round(distances["road"] * MODE_FACTORS["car"]["g_per_passenger_km"] * passengers / 1000, 2)
    flight_baseline = round(distances["air"] * MODE_FACTORS["flight"]["g_per_passenger_km"] * passengers / 1000, 2)
    saved = max(0, round(car_baseline - co2_kg, 2))
    reward = round(saved * (2.5 if preference == Preference.eco else 1.2 if preference == Preference.balanced else 0.35))
    reliability = round(sum(segment["reliability"] for segment in segments) / len(segments))
    map_points = interpolate_points(a, b, bends=max(2, len(segments)), offset={"eco": 0.42, "balanced": 0.14, "fast": -0.26}[preference.value])
    title = {"eco": "Eco route", "balanced": "Balanced route", "fast": "Fast route"}[preference.value]
    return {
        "id": f"{a['id']}-{b['id']}-{preference.value}-{passengers}-{int(luggage_kg)}",
        "preference": preference.value,
        "title": title,
        "from": a,
        "to": b,
        "distanceKm": distance_km,
        "directDistanceKm": distances["direct"],
        "durationMin": duration,
        "co2Kg": co2_kg,
        "baselineCarCo2Kg": car_baseline,
        "baselineFlightCo2Kg": flight_baseline,
        "co2SavedKg": saved,
        "rewardPoints": reward,
        "reliability": reliability,
        "transfers": max(0, len(segments) - 1),
        "segments": segments,
        "map": {
            "center": {"lat": round((a["lat"] + b["lat"]) / 2, 5), "lng": round((a["lng"] + b["lng"]) / 2, 5)},
            "points": map_points,
            "bounds": [
                [min(a["lat"], b["lat"]) - 1.0, min(a["lng"], b["lng"]) - 1.0],
                [max(a["lat"], b["lat"]) + 1.0, max(a["lng"], b["lng"]) + 1.0],
            ],
        },
        "calculation": {
            "formula": "segment kgCO2e = km x g/passenger-km x regional/congestion multiplier x luggage multiplier x passengers / 1000",
            "passengers": passengers,
            "luggageKg": luggage_kg,
            "regionalGridMultiplier": round((REGION_GRID_INTENSITY[a["region"]] + REGION_GRID_INTENSITY[b["region"]]) / 2, 2),
            "carBaselineFactorGPerKm": MODE_FACTORS["car"]["g_per_passenger_km"],
        },
        "score": round((saved * 3.8) + (reliability * 0.7) - (duration / 22) - (len(segments) * 1.8), 1),
    }


def routes_between(from_id: str, to_id: str, passengers: int = 1, luggage_kg: float = 8) -> list[dict[str, Any]]:
    a = place_by_id(from_id)
    b = place_by_id(to_id)
    if not a or not b or a["id"] == b["id"]:
        raise HTTPException(status_code=400, detail="Choose two different supported places.")
    distances = distance_profile(a, b)
    routes = [route_payload(pref, a, b, distances, passengers, luggage_kg) for pref in Preference]
    return sorted(routes, key=lambda route: route["score"], reverse=True)


app = FastAPI(title="GreenRoute India API", version="2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "framework": "FastAPI"}


@app.get("/api/places")
def places() -> dict[str, Any]:
    return {"places": PLACES, "count": len(PLACES)}


@app.get("/api/routes")
def routes(
    from_id: str = Query(alias="from"),
    to_id: str = Query(alias="to"),
    passengers: int = Query(default=1, ge=1, le=8),
    luggage_kg: float = Query(default=8, ge=0, le=80, alias="luggageKg"),
) -> dict[str, Any]:
    return {"routes": routes_between(from_id, to_id, passengers, luggage_kg)}


@app.post("/api/trips", status_code=201)
def save_trip(request: SaveTripRequest) -> dict[str, Any]:
    routes = routes_between(request.fromId, request.toId, request.passengers, request.luggageKg)
    selected = next((route for route in routes if route["id"] == request.routeId), None)
    if not selected:
        raise HTTPException(status_code=400, detail="Route could not be saved.")
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute(
            """
            INSERT INTO trips
            (created_at, route_id, preference, from_name, to_name, distance_km, duration_min, co2_kg, reward_points)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now(timezone.utc).isoformat(),
                selected["id"],
                selected["preference"],
                selected["from"]["name"],
                selected["to"]["name"],
                selected["distanceKm"],
                selected["durationMin"],
                selected["co2Kg"],
                selected["rewardPoints"],
            ),
        )
        conn.commit()
    return {"tripId": cursor.lastrowid, "savedTrip": selected}


@app.get("/api/history")
def history() -> dict[str, Any]:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        trips = [dict(row) for row in conn.execute("SELECT * FROM trips ORDER BY id DESC LIMIT 20")]
        points = conn.execute("SELECT COALESCE(SUM(reward_points), 0) FROM trips").fetchone()[0]
        saved = conn.execute("SELECT COALESCE(SUM((distance_km * 0.178) - co2_kg), 0) FROM trips").fetchone()[0]
        total = conn.execute("SELECT COUNT(*) FROM trips").fetchone()[0]
    return {"trips": trips, "rewardPoints": points, "co2SavedKg": round(saved, 2), "totalTrips": total}


if __name__ == "__main__":
    uvicorn.run("server:app", host=HOST, port=PORT, reload=False)
