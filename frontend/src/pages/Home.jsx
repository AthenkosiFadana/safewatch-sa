import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../services/api'
import { useAuth } from '../context/AuthContext'
import IncidentMap from '../components/IncidentMap'
import DashboardCard from '../components/DashboardCard'
import IncidentCard from '../components/IncidentCard'

export default function Home() {
  const { user } = useAuth()
  const [stats, setStats] = useState({ active: 0, warnings: 0, total: 0 })
  const [recent, setRecent] = useState([])
  const [incidents, setIncidents] = useState([])

  useEffect(() => {
    api.listIncidents().then((data) => {
      const open = data.incidents.filter((i) =>
        ['PENDING', 'UNDER_REVIEW', 'VERIFIED'].includes(i.status)
      )
      setIncidents(open.slice(0, 40))
      setStats({
        active: open.filter((i) => i.severity === 'HIGH' || i.severity === 'CRITICAL').length,
        warnings: open.length,
        total: data.count,
      })
      setRecent(data.incidents.slice(0, 6))
    }).catch(() => {})
    api.listAlerts().then((d) => setStats((s) => ({ ...s, alerts: d.alerts.length }))).catch(() => {})
  }, [])

  return (
    <div>
      <section className="bg-gradient-to-br from-slate-900 via-slate-800 to-red-950 text-white">
        <div className="mx-auto max-w-7xl px-4 py-16 sm:py-24">
          <p className="text-sm font-semibold uppercase tracking-widest text-red-400">
            Community crime &amp; safety monitoring
          </p>
          <h1 className="mt-3 max-w-3xl text-4xl font-bold leading-tight sm:text-5xl">
            See it. Report it. Stay informed.
          </h1>
          <p className="mt-4 max-w-2xl text-slate-300">
            SafeWatch SA lets communities report safety incidents, watch crime patterns on an
            interactive map, and receive local alerts — built for South African neighbourhoods.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link to="/report" className="rounded-lg bg-red-600 px-5 py-3 font-semibold hover:bg-red-700">
              Report Incident
            </Link>
            <Link to="/map" className="rounded-lg border border-white/30 px-5 py-3 font-semibold hover:bg-white/10">
              View Map
            </Link>
            <Link to="/alerts" className="rounded-lg border border-white/30 px-5 py-3 font-semibold hover:bg-white/10">
              Safety Alerts
            </Link>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-4 py-10">
        <div className="grid gap-4 sm:grid-cols-3">
          <DashboardCard title="Active Incidents" value={stats.active} icon="🔴" accent="text-red-600" hint="High & critical severity, unresolved" />
          <DashboardCard title="Warnings" value={stats.warnings} icon="🟡" accent="text-yellow-600" hint="Open reports awaiting resolution" />
          <DashboardCard title="Active Alerts" value={stats.alerts ?? 0} icon="⚠️" accent="text-amber-600" hint="Area clusters in the last 2 hours" />
        </div>

        <div className="mt-8 grid gap-6 lg:grid-cols-3">
          <div className="lg:col-span-2">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-lg font-bold text-slate-900">Live incident map</h2>
              <Link to="/map" className="text-sm font-semibold text-red-600 hover:underline">Full map →</Link>
            </div>
            <IncidentMap incidents={incidents} height="h-[420px]" />
            <p className="mt-2 text-xs text-slate-400">
              🟢 Low · 🟡 Medium · 🟠 High · 🔴 Critical
            </p>
          </div>
          <div>
            <h2 className="mb-3 text-lg font-bold text-slate-900">Latest reports</h2>
            <div className="flex flex-col gap-3">
              {recent.map((i) => <IncidentCard key={i.incidentId} incident={i} />)}
              {!recent.length && <p className="text-sm text-slate-500">No reports yet.</p>}
            </div>
          </div>
        </div>
      </section>

      <section className="border-t border-slate-200 bg-slate-50">
        <div className="mx-auto grid max-w-7xl gap-6 px-4 py-12 sm:grid-cols-3">
          {[
            ['🚨', 'Report', 'Log theft, vandalism, suspicious activity or road incidents in seconds.'],
            ['🗺️', 'Visualise', 'See hotspots on an interactive map coloured by severity.'],
            ['🔔', 'Stay informed', 'Automatic cluster alerts when incidents spike in your area.'],
          ].map(([icon, title, text]) => (
            <div key={title} className="rounded-xl border border-slate-200 bg-white p-6">
              <div className="text-3xl">{icon}</div>
              <h3 className="mt-3 font-bold text-slate-900">{title}</h3>
              <p className="mt-1 text-sm text-slate-600">{text}</p>
            </div>
          ))}
        </div>
      </section>

      {!user && (
        <section className="mx-auto max-w-7xl px-4 py-12 text-center">
          <h2 className="text-2xl font-bold text-slate-900">Join your community watch</h2>
          <p className="mt-2 text-slate-600">Register to report incidents and receive local safety alerts.</p>
          <Link to="/register" className="mt-4 inline-block rounded-lg bg-slate-900 px-6 py-3 font-semibold text-white hover:bg-slate-700">
            Create free account
          </Link>
        </section>
      )}
    </div>
  )
}
