import { useEffect, useState } from 'react'
import api from '../services/api'
import DashboardCard from '../components/DashboardCard'
import { categoryLabel, formatDateTime } from '../constants'
import { SeverityBadge, StatusBadge } from '../components/Badges'

const FLOW = ['PENDING', 'UNDER_REVIEW', 'VERIFIED', 'RESOLVED']

export default function Admin() {
  const [stats, setStats] = useState(null)
  const [reports, setReports] = useState([])
  const [error, setError] = useState('')
  const [busy, setBusy] = useState('')

  const load = () =>
    Promise.all([api.adminStats(), api.adminReports()])
      .then(([s, r]) => {
        setStats(s)
        setReports(r)
      })
      .catch((e) => setError(e.message))

  useEffect(() => { load() }, [])

  async function moderate(id, status) {
    setBusy(id)
    try {
      await api.moderateIncident(id, status)
      await load()
    } catch (e) {
      setError(e.message)
    } finally {
      setBusy('')
    }
  }

  if (error) return <div className="mx-auto max-w-7xl px-4 py-8 text-rose-600">{error}</div>
  if (!stats) return <div className="mx-auto max-w-7xl px-4 py-8 text-slate-500">Loading admin dashboard…</div>

  return (
    <div className="mx-auto max-w-7xl px-4 py-8">
      <h1 className="text-2xl font-bold text-slate-900">Admin Dashboard</h1>
      <p className="text-sm text-slate-500">Moderation queue, platform statistics and abuse detection.</p>

      <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <DashboardCard title="Total incidents" value={stats.totalIncidents.toLocaleString()} icon="📋" />
        <DashboardCard title="Open incidents" value={stats.openIncidents} icon="🟡" accent="text-yellow-600" />
        <DashboardCard title="Resolved incidents" value={stats.resolvedIncidents} icon="✅" accent="text-emerald-600" />
        <DashboardCard title="Active alerts" value={stats.activeAlerts} icon="⚠️" accent="text-red-600" />
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-3">
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="mb-4 font-bold text-slate-900">Most reported</h2>
          <ul className="space-y-3">
            {stats.categoryBreakdown.map((c) => (
              <li key={c.category}>
                <div className="flex justify-between text-sm text-slate-700">
                  <span>{categoryLabel(c.category)}</span>
                  <span className="font-semibold">{c.percent}%</span>
                </div>
                <div className="mt-1 h-2 rounded-full bg-slate-100">
                  <div className="h-2 rounded-full bg-slate-900" style={{ width: `${c.percent}%` }} />
                </div>
              </li>
            ))}
          </ul>
          <div className="mt-4 grid grid-cols-2 gap-2 text-xs text-slate-500">
            <p>Rejected: <strong>{stats.rejectedIncidents}</strong></p>
            <p>Duplicate flagged: <strong>{stats.duplicateFlagged}</strong></p>
          </div>
        </div>

        <div className="lg:col-span-2">
          <h2 className="mb-3 text-lg font-bold text-slate-900">Moderation queue</h2>
          <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm">
            <table className="min-w-full text-left text-sm">
              <thead className="border-b border-slate-200 bg-slate-50 text-xs uppercase text-slate-500">
                <tr>
                  <th className="px-4 py-3">Incident</th>
                  <th className="px-4 py-3">Area</th>
                  <th className="px-4 py-3">Severity</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Reported</th>
                  <th className="px-4 py-3">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {stats.pendingQueue.map((i) => (
                  <tr key={i.incidentId} className="hover:bg-slate-50">
                    <td className="px-4 py-3">
                      <p className="font-medium text-slate-800">{categoryLabel(i.category)}</p>
                      <p className="text-xs text-slate-400">{i.incidentId}</p>
                    </td>
                    <td className="px-4 py-3 text-slate-600">{i.area}</td>
                    <td className="px-4 py-3"><SeverityBadge severity={i.severity} /></td>
                    <td className="px-4 py-3"><StatusBadge status={i.status} /></td>
                    <td className="px-4 py-3 text-xs text-slate-500">{formatDateTime(i.createdAt)}</td>
                    <td className="px-4 py-3">
                      <div className="flex flex-wrap gap-1">
                        {FLOW[FLOW.indexOf(i.status) + 1] && (
                          <button
                            disabled={busy === i.incidentId}
                            onClick={() => moderate(i.incidentId, FLOW[FLOW.indexOf(i.status) + 1])}
                            className="rounded bg-emerald-600 px-2 py-1 text-xs font-semibold text-white hover:bg-emerald-700 disabled:opacity-50"
                          >
                            Advance
                          </button>
                        )}
                        {i.status !== 'REJECTED' && (
                          <button
                            disabled={busy === i.incidentId}
                            onClick={() => moderate(i.incidentId, 'REJECTED')}
                            className="rounded bg-rose-600 px-2 py-1 text-xs font-semibold text-white hover:bg-rose-700 disabled:opacity-50"
                          >
                            Reject
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
                {!stats.pendingQueue.length && (
                  <tr><td colSpan={6} className="px-4 py-6 text-center text-slate-400">Queue is clear 🎉</td></tr>
                )}
              </tbody>
            </table>
          </div>

          <h2 className="mb-3 mt-6 text-lg font-bold text-slate-900">Reporter activity (24h)</h2>
          <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm">
            <table className="min-w-full text-left text-sm">
              <thead className="border-b border-slate-200 bg-slate-50 text-xs uppercase text-slate-500">
                <tr>
                  <th className="px-4 py-3">User</th>
                  <th className="px-4 py-3">Reports</th>
                  <th className="px-4 py-3">Flag</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {reports.map((r) => (
                  <tr key={r.userId}>
                    <td className="px-4 py-3 font-mono text-xs">{r.userId}</td>
                    <td className="px-4 py-3">{r.reports24h}</td>
                    <td className="px-4 py-3">
                      {r.flagged
                        ? <span className="rounded-full bg-amber-100 px-2 py-0.5 text-xs font-semibold text-amber-800">Rate-limit watch</span>
                        : <span className="text-xs text-slate-400">normal</span>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  )
}
