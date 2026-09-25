import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { categoryLabel, formatDateTime } from '../constants'

export default function AlertCard({ alert }) {
  const [time, setTime] = useState('')
  useEffect(() => setTime(formatDateTime(alert.createdAt)), [alert.createdAt])

  return (
    <div className="rounded-xl border border-amber-300 bg-amber-50 p-4 shadow-sm">
      <div className="flex items-center gap-2">
        <span className="text-xl">⚠️</span>
        <h3 className="font-bold text-amber-900">SAFETY ALERT — {alert.area}</h3>
      </div>
      <p className="mt-2 text-sm text-amber-900">{alert.message}</p>
      <dl className="mt-3 grid grid-cols-2 gap-2 text-sm text-amber-900">
        <div>
          <dt className="text-xs uppercase tracking-wide text-amber-700">Incidents</dt>
          <dd className="font-semibold">{alert.incidentIds?.length || 0}</dd>
        </div>
        <div>
          <dt className="text-xs uppercase tracking-wide text-amber-700">Primary category</dt>
          <dd className="font-semibold">{categoryLabel(alert.category)}</dd>
        </div>
      </dl>
      <div className="mt-3 flex items-center justify-between text-xs text-amber-700">
        <span>{time}</span>
        <span className="rounded-full bg-amber-200 px-2 py-0.5 font-semibold uppercase">{alert.status}</span>
      </div>
    </div>
  )
}

export function EmptyAlerts() {
  return (
    <div className="rounded-xl border border-dashed border-slate-300 bg-white p-8 text-center text-slate-500">
      <p className="text-2xl">✅</p>
      <p className="mt-2 font-medium">No active safety alerts</p>
      <p className="text-sm">Alerts are raised automatically when several incidents hit the same area within 2 hours.</p>
      <Link to="/map" className="mt-3 inline-block text-sm font-semibold text-red-600 hover:underline">
        View the incident map →
      </Link>
    </div>
  )
}
