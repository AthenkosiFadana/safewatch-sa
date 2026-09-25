import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../services/api'
import { useAuth } from '../context/AuthContext'
import DashboardCard from '../components/DashboardCard'
import IncidentCard from '../components/IncidentCard'
import AlertCard, { EmptyAlerts } from '../components/AlertCard'

export default function Dashboard() {
  const { user } = useAuth()
  const [incidents, setIncidents] = useState([])
  const [alerts, setAlerts] = useState([])
  const [analytics, setAnalytics] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    api.listIncidents().then((d) => setIncidents(d.incidents)).catch((e) => setError(e.message))
    api.listAlerts(user?.community).then((d) => setAlerts(d.alerts.slice(0, 3))).catch(() => {})
    api.analytics().then(setAnalytics).catch(() => {})
  }, [user?.community])

  const open = incidents.filter((i) => ['PENDING', 'UNDER_REVIEW', 'VERIFIED'].includes(i.status))
  const mine = incidents.filter((i) => i.userId === user?.userId)

  return (
    <div className="mx-auto max-w-7xl px-4 py-8">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Community Safety Dashboard</h1>
          <p className="text-sm text-slate-500">
            {user?.community ? `Your community: ${user.community}` : 'All reported areas'} · Welcome, {user?.name}
          </p>
        </div>
        <div className="flex gap-2">
          <Link to="/report" className="rounded-lg bg-red-600 px-4 py-2 text-sm font-semibold text-white hover:bg-red-700">
            Report Incident
          </Link>
          <Link to="/map" className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50">
            View Map
          </Link>
        </div>
      </div>

      {error && <p className="mt-4 rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</p>}

      <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <DashboardCard title="Active Incidents" value={open.length} icon="🔴" accent="text-red-600" />
        <DashboardCard title="Total Reports" value={incidents.length} icon="📋" />
        <DashboardCard title="Active Alerts" value={alerts.filter((a) => a.status === 'ACTIVE').length} icon="⚠️" accent="text-amber-600" />
        <DashboardCard title="My Reports" value={mine.length} icon="✍️" accent="text-blue-600" />
      </div>

      <div className="mt-8 grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <h2 className="mb-3 text-lg font-bold text-slate-900">Latest incidents</h2>
          <div className="grid gap-3 sm:grid-cols-2">
            {incidents.slice(0, 8).map((i) => <IncidentCard key={i.incidentId} incident={i} />)}
            {!incidents.length && <p className="text-sm text-slate-500">No incidents recorded yet.</p>}
          </div>
        </div>

        <div>
          <h2 className="mb-3 text-lg font-bold text-slate-900">Safety alerts</h2>
          <div className="flex flex-col gap-3">
            {alerts.length ? alerts.map((a) => <AlertCard key={a.alertId} alert={a} />) : <EmptyAlerts />}
          </div>

          {analytics && (
            <div className="mt-6 rounded-xl border border-slate-200 bg-white p-4">
              <h3 className="font-bold text-slate-900">Top categories</h3>
              <ul className="mt-3 space-y-2">
                {analytics.byCategory.slice(0, 5).map((c) => (
                  <li key={c.key}>
                    <div className="flex justify-between text-sm text-slate-600">
                      <span>{c.key.replace('_', ' ').toLowerCase()}</span>
                      <span className="font-semibold">{c.percent}%</span>
                    </div>
                    <div className="mt-1 h-2 rounded-full bg-slate-100">
                      <div className="h-2 rounded-full bg-red-500" style={{ width: `${c.percent}%` }} />
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
