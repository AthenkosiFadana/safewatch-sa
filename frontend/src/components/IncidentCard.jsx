import { Link } from 'react-router-dom'
import { categoryLabel, formatDateTime } from '../constants'
import { SeverityBadge, StatusBadge } from './Badges'

export default function IncidentCard({ incident }) {
  return (
    <Link
      to={`/incidents/${incident.incidentId}`}
      className="block rounded-xl border border-slate-200 bg-white p-4 shadow-sm transition hover:border-slate-300 hover:shadow-md"
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="font-semibold text-slate-900">{categoryLabel(incident.category)}</p>
          <p className="text-xs text-slate-500">{incident.area}</p>
        </div>
        <SeverityBadge severity={incident.severity} />
      </div>
      <p className="mt-2 line-clamp-2 text-sm text-slate-600">{incident.description}</p>
      <div className="mt-3 flex items-center justify-between text-xs text-slate-500">
        <span>{formatDateTime(incident.createdAt)}</span>
        <StatusBadge status={incident.status} />
      </div>
      {incident.duplicateOf && (
        <p className="mt-2 rounded bg-amber-50 px-2 py-1 text-xs text-amber-700">
          Possibly related to {incident.duplicateOf}
        </p>
      )}
    </Link>
  )
}
