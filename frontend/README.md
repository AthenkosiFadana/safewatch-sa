# SafeWatch SA — Frontend

React + Vite client for SafeWatch SA.

## Stack

- **React 19** + **Vite 5**
- **Tailwind CSS 4** (via `@tailwindcss/vite`)
- **React Router** — page routing and protected routes
- **Leaflet / react-leaflet** — interactive incident map (OpenStreetMap tiles)
- **Recharts** — analytics charts

## Run

```bash
npm install
npm run dev        # http://localhost:5173
```

The dev server proxies `/api` to the Flask backend on `http://127.0.0.1:5001`
(see `vite.config.js`). To point at a deployed API instead, create `.env.local`:

```
VITE_API_URL=https://<function-url>   # ApiMode=functionurl
```

## Build

```bash
npm run build      # production bundle in dist/
npm run lint       # oxlint
```

## Structure

```
src/
├── components/   Navbar, Footer, IncidentCard, IncidentMap, AlertCard,
│                 DashboardCard, Badges, ProtectedRoute
├── pages/        Home, Login, Register, Dashboard, ReportIncident,
│                 MapPage, IncidentDetail, Alerts, Analytics, Admin, Profile
├── context/      AuthContext (JWT stored in localStorage)
├── services/     api.js — fetch wrapper with auth header + error handling
└── constants.js  categories, severities, statuses, areas, formatters
```
