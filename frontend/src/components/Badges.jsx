import { SEVERITY_META, STATUS_META } from '../constants'

export function SeverityBadge({ severity }) {
  const meta = SEVERITY_META[severity] || SEVERITY_META.LOW
  return (
    <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-semibold ${meta.bg}`}>
      <span className="h-2 w-2 rounded-full" style={{ backgroundColor: meta.color }} />
      {meta.label}
    </span>
  )
}

export function StatusBadge({ status }) {
  const meta = STATUS_META[status] || STATUS_META.PENDING
  return (
    <span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-semibold ${meta.bg}`}>
      {meta.label}
    </span>
  )
}
