import React from "react";
import { createRoot } from "react-dom/client";
import { QueryClient, QueryClientProvider, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Alert,
  Box,
  Button,
  Chip,
  CssBaseline,
  Divider,
  FormControl,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Slider,
  Stack,
  Tab,
  Tabs,
  ThemeProvider,
  Typography,
  createTheme,
} from "@mui/material";
import { MapContainer, Polyline, TileLayer, CircleMarker, Popup, useMap } from "react-leaflet";
import { Bar, BarChart, CartesianGrid, Cell, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import {
  Bus,
  CarFront,
  Clock3,
  Footprints,
  History,
  Leaf,
  Luggage,
  MapPinned,
  Navigation,
  Plane,
  RefreshCw,
  Route,
  ShieldCheck,
  Sparkles,
  TrainFront,
  Trophy,
  Users,
  Zap,
} from "lucide-react";
import "leaflet/dist/leaflet.css";
import "./styles.css";

const API_BASE = "http://127.0.0.1:8000";

const queryClient = new QueryClient();

const theme = createTheme({
  palette: {
    mode: "light",
    primary: { main: "#236b4b" },
    secondary: { main: "#265f96" },
    warning: { main: "#b95c3b" },
    background: { default: "#eef3f0", paper: "#ffffff" },
  },
  shape: { borderRadius: 8 },
  typography: {
    fontFamily: 'Inter, "Segoe UI", system-ui, sans-serif',
    h1: { fontWeight: 900, letterSpacing: 0 },
    h2: { fontWeight: 850, letterSpacing: 0 },
    h3: { fontWeight: 850, letterSpacing: 0 },
    button: { fontWeight: 800, textTransform: "none" },
  },
  components: {
    MuiPaper: { styleOverrides: { root: { backgroundImage: "none" } } },
    MuiButton: { styleOverrides: { root: { minHeight: 42 } } },
  },
});

const FALLBACK_PLACES = [
  { id: "delhi", name: "Delhi", state: "Delhi", lat: 28.6139, lng: 77.209, region: "north", transit: 91 },
  { id: "mumbai", name: "Mumbai", state: "Maharashtra", lat: 19.076, lng: 72.8777, region: "west", transit: 94 },
  { id: "bengaluru", name: "Bengaluru", state: "Karnataka", lat: 12.9716, lng: 77.5946, region: "south", transit: 82 },
  { id: "chennai", name: "Chennai", state: "Tamil Nadu", lat: 13.0827, lng: 80.2707, region: "south", transit: 86 },
  { id: "kolkata", name: "Kolkata", state: "West Bengal", lat: 22.5726, lng: 88.3639, region: "east", transit: 89 },
  { id: "hyderabad", name: "Hyderabad", state: "Telangana", lat: 17.385, lng: 78.4867, region: "south", transit: 80 },
];

const preferenceMeta = {
  eco: { label: "Eco", color: "#27724f", icon: Leaf, tone: "Lowest CO2" },
  balanced: { label: "Balanced", color: "#286aa0", icon: Sparkles, tone: "Time and carbon" },
  fast: { label: "Fast", color: "#c05c3d", icon: Zap, tone: "Shortest time" },
};

const modeIcons = {
  walk: Footprints,
  cycle: Navigation,
  metro: TrainFront,
  bus: Bus,
  train: TrainFront,
  ev: Zap,
  car: CarFront,
  flight: Plane,
};

function minutesToText(total) {
  const hours = Math.floor(total / 60);
  const minutes = total % 60;
  return hours ? `${hours}h ${minutes}m` : `${minutes} min`;
}

async function fetchJson(path, options) {
  const response = await fetch(`${API_BASE}${path}`, options);
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(payload.detail || payload.error || "Request failed");
  return payload;
}

function FitMap({ bounds, routeId }) {
  const map = useMap();
  React.useEffect(() => {
    if (bounds?.length === 2) {
      map.fitBounds(bounds, { padding: [24, 24] });
      setTimeout(() => map.invalidateSize(), 80);
    }
  }, [bounds, map, routeId]);
  return null;
}

function RouteMap({ route, compact = false }) {
  if (!route?.map?.points?.length) {
    return <div className="map-empty">No route map available</div>;
  }
  const color = preferenceMeta[route.preference].color;
  const points = route.map.points.map((point) => [point.lat, point.lng]);

  return (
    <div className={compact ? "route-map compact" : "route-map"}>
      <MapContainer center={[route.map.center.lat, route.map.center.lng]} zoom={5} scrollWheelZoom={!compact} attributionControl={!compact}>
        <TileLayer
          attribution="&copy; OpenStreetMap contributors"
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <FitMap bounds={route.map.bounds} routeId={route.id} />
        <Polyline positions={points} pathOptions={{ color, weight: compact ? 4 : 6, opacity: 0.9 }} />
        <CircleMarker center={points[0]} radius={compact ? 5 : 7} pathOptions={{ color: "#18573c", fillColor: "#ffffff", fillOpacity: 1 }}>
          <Popup>{route.from.name}</Popup>
        </CircleMarker>
        <CircleMarker center={points[points.length - 1]} radius={compact ? 5 : 7} pathOptions={{ color: "#a5452d", fillColor: "#ffffff", fillOpacity: 1 }}>
          <Popup>{route.to.name}</Popup>
        </CircleMarker>
      </MapContainer>
    </div>
  );
}

function Stat({ icon: Icon, label, value }) {
  return (
    <div className="stat">
      <Icon size={18} />
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function RouteCard({ route, selected, onSelect, onSave, saving }) {
  const meta = preferenceMeta[route.preference];
  const Icon = meta.icon;
  return (
    <Paper className={`route-card ${selected ? "selected" : ""}`} elevation={0}>
      <button className="route-select" onClick={onSelect}>
        <div className="route-card-head">
          <span className="route-title" style={{ color: meta.color }}>
            <Icon size={20} />
            {route.title}
          </span>
          <Chip size="small" label={`${route.score} score`} />
        </div>
      </button>
      <div className="route-card-body">
        <RouteMap route={route} compact />
        <div className="route-stat-grid">
          <Stat icon={Leaf} label="CO2" value={`${route.co2Kg} kg`} />
          <Stat icon={Clock3} label="Time" value={minutesToText(route.durationMin)} />
          <Stat icon={Route} label="Distance" value={`${route.distanceKm} km`} />
          <Stat icon={Trophy} label="Rewards" value={`${route.rewardPoints} pts`} />
        </div>
      </div>
      {selected && (
        <Button className="save-button" variant="contained" startIcon={saving ? <RefreshCw className="spin" size={17} /> : <Trophy size={17} />} onClick={onSave}>
          Save selected route
        </Button>
      )}
    </Paper>
  );
}

function SegmentTimeline({ route }) {
  return (
    <Paper className="panel" elevation={0}>
      <div className="section-title">
        <Navigation size={18} />
        <Typography variant="h3">Segment Details</Typography>
      </div>
      <Stack divider={<Divider flexItem />} spacing={0}>
        {route.segments.map((segment, index) => {
          const Icon = modeIcons[segment.mode] || Route;
          return (
            <div className="segment-row" key={`${segment.mode}-${index}`}>
              <span className="segment-icon"><Icon size={18} /></span>
              <div>
                <strong>{segment.label}</strong>
                <p>{segment.description}</p>
                <small>
                  {segment.distanceKm} km, {minutesToText(segment.durationMin)}, {segment.co2Kg} kg CO2e,
                  {` ${segment.gPerPassengerKm} g/passenger-km`}
                </small>
              </div>
            </div>
          );
        })}
      </Stack>
    </Paper>
  );
}

function ComparisonChart({ routes }) {
  const data = routes.map((route) => ({
    name: preferenceMeta[route.preference].label,
    CO2: route.co2Kg,
    "Car baseline": route.baselineCarCo2Kg,
    "Duration hrs": Number((route.durationMin / 60).toFixed(1)),
  }));
  return (
    <Paper className="panel chart-panel" elevation={0}>
      <div className="section-title">
        <ShieldCheck size={18} />
        <Typography variant="h3">Route Comparison</Typography>
      </div>
      <ResponsiveContainer width="100%" height={260}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} />
          <XAxis dataKey="name" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Bar dataKey="CO2">
            {routes.map((route) => <Cell key={route.id} fill={preferenceMeta[route.preference].color} />)}
          </Bar>
          <Bar dataKey="Car baseline" fill="#a8b7b0" />
          <Bar dataKey="Duration hrs" fill="#d3a84a" />
        </BarChart>
      </ResponsiveContainer>
    </Paper>
  );
}

function CalculationPanel({ route }) {
  const calc = route.calculation;
  return (
    <Paper className="panel" elevation={0}>
      <div className="section-title">
        <Leaf size={18} />
        <Typography variant="h3">CO2 Calculation</Typography>
      </div>
      <div className="formula">{calc.formula}</div>
      <div className="calc-grid">
        <Stat icon={Users} label="Passengers" value={calc.passengers} />
        <Stat icon={Luggage} label="Luggage" value={`${calc.luggageKg} kg`} />
        <Stat icon={CarFront} label="Car baseline" value={`${route.baselineCarCo2Kg} kg`} />
        <Stat icon={Plane} label="Flight baseline" value={`${route.baselineFlightCo2Kg} kg`} />
        <Stat icon={ShieldCheck} label="Reliability" value={`${route.reliability}%`} />
        <Stat icon={Leaf} label="CO2 saved" value={`${route.co2SavedKg} kg`} />
      </div>
    </Paper>
  );
}

function HistoryPanel({ history }) {
  return (
    <Paper className="history-panel" elevation={0}>
      <div className="section-title">
        <History size={18} />
        <Typography variant="h3">Previous Travel</Typography>
      </div>
      <div className="history-summary">
        <Stat icon={Trophy} label="Reward points" value={history?.rewardPoints || 0} />
        <Stat icon={Leaf} label="CO2 saved" value={`${history?.co2SavedKg || 0} kg`} />
      </div>
      <div className="history-list">
        {!history?.trips?.length && <p className="muted">Saved trips will appear here.</p>}
        {history?.trips?.map((trip) => (
          <div className="history-item" key={trip.id}>
            <strong>{trip.from_name} to {trip.to_name}</strong>
            <span>{trip.preference} route, {minutesToText(trip.duration_min)}, {trip.reward_points} pts</span>
          </div>
        ))}
      </div>
    </Paper>
  );
}

function PlannerApp() {
  const [fromId, setFromId] = React.useState("delhi");
  const [toId, setToId] = React.useState("mumbai");
  const [passengers, setPassengers] = React.useState(1);
  const [luggageKg, setLuggageKg] = React.useState(8);
  const [selectedRouteId, setSelectedRouteId] = React.useState("");
  const [tab, setTab] = React.useState("overview");
  const queryClientInstance = useQueryClient();

  const placesQuery = useQuery({
    queryKey: ["places"],
    queryFn: () => fetchJson("/api/places"),
    staleTime: 1000 * 60 * 10,
  });

  const routesQuery = useQuery({
    queryKey: ["routes", fromId, toId, passengers, luggageKg],
    queryFn: () => fetchJson(`/api/routes?from=${fromId}&to=${toId}&passengers=${passengers}&luggageKg=${luggageKg}`),
    enabled: fromId !== toId,
  });

  const historyQuery = useQuery({
    queryKey: ["history"],
    queryFn: () => fetchJson("/api/history"),
  });

  const saveMutation = useMutation({
    mutationFn: (route) => fetchJson("/api/trips", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ fromId, toId, routeId: route.id, passengers, luggageKg }),
    }),
    onSuccess: () => queryClientInstance.invalidateQueries({ queryKey: ["history"] }),
  });

  const places = placesQuery.data?.places || FALLBACK_PLACES;
  const routes = routesQuery.data?.routes || [];
  const selectedRoute = routes.find((route) => route.id === selectedRouteId) || routes[0];

  React.useEffect(() => {
    if (routes.length && !routes.some((route) => route.id === selectedRouteId)) {
      setSelectedRouteId(routes[0].id);
    }
  }, [routes, selectedRouteId]);

  const error = placesQuery.error?.message || routesQuery.error?.message || historyQuery.error?.message;

  return (
    <Box className="app-shell">
      <CssBaseline />
      <Box className="planner-shell">
        <Box className="topbar">
          <div>
            <span className="brand"><Leaf size={23} /> GreenRoute India</span>
            <Typography variant="h1">Multi-modal route planning with transparent carbon math</Typography>
          </div>
          <Stack direction="row" spacing={1} sx={{ flexWrap: "wrap", rowGap: 1 }}>
            <Chip icon={<ShieldCheck size={16} />} label="FastAPI backend" />
            <Chip icon={<MapPinned size={16} />} label="Leaflet route maps" />
            <Chip icon={<Sparkles size={16} />} label="React Query state" />
          </Stack>
        </Box>

        <Paper className="search-panel" elevation={0}>
          <FormControl size="small">
            <InputLabel>From</InputLabel>
            <Select label="From" value={fromId} onChange={(event) => setFromId(event.target.value)}>
              {places.map((place) => <MenuItem value={place.id} key={place.id}>{place.name}, {place.state}</MenuItem>)}
            </Select>
          </FormControl>
          <Button variant="outlined" aria-label="Swap places" onClick={() => { setFromId(toId); setToId(fromId); }}>
            <RefreshCw size={18} />
          </Button>
          <FormControl size="small">
            <InputLabel>To</InputLabel>
            <Select label="To" value={toId} onChange={(event) => setToId(event.target.value)}>
              {places.map((place) => <MenuItem value={place.id} key={place.id}>{place.name}, {place.state}</MenuItem>)}
            </Select>
          </FormControl>
          <div className="slider-control">
            <span><Users size={16} /> Passengers: {passengers}</span>
            <Slider min={1} max={8} step={1} marks value={passengers} onChange={(_, value) => setPassengers(value)} />
          </div>
          <div className="slider-control">
            <span><Luggage size={16} /> Luggage: {luggageKg} kg</span>
            <Slider min={0} max={60} step={2} value={luggageKg} onChange={(_, value) => setLuggageKg(value)} />
          </div>
        </Paper>

        {error && <Alert severity="warning">Backend issue: {error}</Alert>}
        {fromId === toId && <Alert severity="info">Choose two different places to calculate routes.</Alert>}

        {selectedRoute && (
          <>
            <Tabs value={tab} onChange={(_, value) => setTab(value)} className="tabs">
              <Tab value="overview" label="Overview" />
              <Tab value="maps" label="Route maps" />
              <Tab value="calculation" label="Calculation" />
            </Tabs>

            {tab === "overview" && (
              <div className="dashboard-grid">
                <div className="route-list">
                  {routes.map((route) => (
                    <RouteCard
                      key={route.id}
                      route={route}
                      selected={route.id === selectedRoute.id}
                      onSelect={() => setSelectedRouteId(route.id)}
                      onSave={() => saveMutation.mutate(route)}
                      saving={saveMutation.isPending}
                    />
                  ))}
                </div>
                <div className="main-stack">
                  <RouteMap route={selectedRoute} />
                  <ComparisonChart routes={routes} />
                </div>
                <div className="side-stack">
                  <CalculationPanel route={selectedRoute} />
                  <SegmentTimeline route={selectedRoute} />
                </div>
              </div>
            )}

            {tab === "maps" && (
              <div className="all-maps-grid">
                {routes.map((route) => (
                  <Paper className="panel" elevation={0} key={route.id}>
                    <div className="section-title">
                      {React.createElement(preferenceMeta[route.preference].icon, { size: 18 })}
                      <Typography variant="h3">{route.title}</Typography>
                    </div>
                    <RouteMap route={route} />
                    <div className="route-stat-grid after-map">
                      <Stat icon={Leaf} label="CO2" value={`${route.co2Kg} kg`} />
                      <Stat icon={Clock3} label="Time" value={minutesToText(route.durationMin)} />
                      <Stat icon={ShieldCheck} label="Reliability" value={`${route.reliability}%`} />
                      <Stat icon={Trophy} label="Reward" value={`${route.rewardPoints} pts`} />
                    </div>
                  </Paper>
                ))}
              </div>
            )}

            {tab === "calculation" && (
              <div className="calculation-grid">
                <CalculationPanel route={selectedRoute} />
                <SegmentTimeline route={selectedRoute} />
                <ComparisonChart routes={routes} />
              </div>
            )}
          </>
        )}
      </Box>
      <HistoryPanel history={historyQuery.data} />
    </Box>
  );
}

function Root() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={theme}>
        <PlannerApp />
      </ThemeProvider>
    </QueryClientProvider>
  );
}

createRoot(document.getElementById("root")).render(<Root />);
