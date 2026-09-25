import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import api from '../services/api'
import { categoryLabel, formatDateTime } from '../constants'
import { SeverityBadge, StatusBadge } from '../components/Badges'
import IncidentMap from '../components/IncidentMap'

export default function IncidentDetail() {
  const { id } = useParams()
  const [incident, setIncident] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    api.getIncident(id).then((d) => setIncident(d.incident)).catch((e) => setError(e.message))
  }, [id])

  if (error) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-16 text-center">
        <p className="text-rose-600">{error}</p>
        <Link to="/map" className="mt-3 inline-block text-sm font-semibold text-slate-700 underline">Back to map</Link>
      </div>
    )
  }
  if (!incident) return <div className="mx-auto max-w-2xl px-4 py-16 text-center text-slate-500">Loading…</div>

  return (
    <div className="mx-auto max-w-4xl px-4 py-8">
      <Link to="/map" className="text-sm font-semibold text-slate-500 hover:text-slate-800">← Back to map</Link>

      <div className="mt-3 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">🚨 {categoryLabel(incident.category)}</h1>
            <p className="text-sm text-slate-500">Incident ID: {incident.incidentId}</p>
          </div>
          <div className="flex gap-2">
            <SeverityBadge severity={incident.severity} />
            <StatusBadge status={incident.status} />
          </div>
        </div>

        <p className="mt-4 text-slate-700">{incident.description}</p>

        <dl className="mt-6 grid gap-4 sm:grid-cols-2">
          <div className="rounded-lg bg-slate-50 p-3">
            <dt className="text-xs uppercase tracking-wide text-slate-500">Location</dt>
            <dd className="font-medium text-slate-800">{incident.area}</dd>
            <dd className="text-xs text-slate-500">{incident.latitude}, {incident.longitude}</dd>
          </div>
          <div className="rounded-lg bg-slate-50 p-3">
            <dt className="text-xs uppercase tracking-wide text-slate-500">Reported</dt>
            <dd className="font-medium text-slate-800">{formatDateTime(incident.createdAt)}</dd>
          </div>
          <div className="rounded-lg bg-slate-50 p-3">
            <dt className="text-xs uppercase tracking-wide text-slate-500">Source</dt>
            <dd className="font-medium text-slate-800">{incident.source}</dd>
          </div>
          <div className="rounded-lg bg-slate-50 p-3">
            <dt className="text-xs uppercase tracking-wide text-slate-500">Last updated</dt>
            <dd className="font-medium text-slate-800">{formatDateTime(incident.updatedAt)}</dd>
          </div>
        </dl>

        {incident.duplicateOf && (
          <p className="mt-4 rounded-lg bg-amber-50 px-3 py-2 text-sm text-amber-800">
            🔗 Flagged as potentially related to {incident.duplicateOf} (duplicate detection)
          </p>
        )}

        <div className="mt-6">
          <h2 className="mb-2 font-bold text-slate-900">Map</h2>
          <IncidentMap incidents={[incident]} selectedId={incident.incidentId} height="h-[320px]" />
        </div>
      </div>
    </div>
  )
}
