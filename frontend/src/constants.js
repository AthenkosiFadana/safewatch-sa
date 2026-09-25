export const CATEGORIES = [
  { value: 'THEFT', label: 'Theft' },
  { value: 'ROBBERY', label: 'Robbery' },
  { value: 'ASSAULT', label: 'Assault' },
  { value: 'VANDALISM', label: 'Vandalism' },
  { value: 'SUSPICIOUS_ACTIVITY', label: 'Suspicious activity' },
  { value: 'MISSING_PERSON', label: 'Missing person' },
  { value: 'ROAD_INCIDENT', label: 'Road incident' },
  { value: 'FIRE', label: 'Fire' },
  { value: 'OTHER', label: 'Other safety incident' },
]

export const SEVERITIES = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']

export const SEVERITY_META = {
  LOW: { label: 'Low', color: '#16a34a', bg: 'bg-green-100 text-green-800', dot: '🟢' },
  MEDIUM: { label: 'Medium', color: '#eab308', bg: 'bg-yellow-100 text-yellow-800', dot: '🟡' },
  HIGH: { label: 'High', color: '#f97316', bg: 'bg-orange-100 text-orange-800', dot: '🟠' },
  CRITICAL: { label: 'Critical', color: '#dc2626', bg: 'bg-red-100 text-red-800', dot: '🔴' },
}

export const STATUS_META = {
  PENDING: { label: 'Pending', bg: 'bg-slate-100 text-slate-700' },
  UNDER_REVIEW: { label: 'Under Review', bg: 'bg-blue-100 text-blue-700' },
  VERIFIED: { label: 'Verified', bg: 'bg-emerald-100 text-emerald-700' },
  RESOLVED: { label: 'Resolved', bg: 'bg-slate-200 text-slate-600' },
  REJECTED: { label: 'Rejected', bg: 'bg-rose-100 text-rose-700' },
}

export const AREAS = [
  'Central, Gqeberha',
  'New Brighton',
  'KwaMagxaki',
  'Korsten',
  'Summerstrand',
  'Humewood',
  'Mount Pleasant',
  'Motherwell',
  'Kganya Park',
  'Saldanha Bay',
]

export const categoryLabel = (value) =>
  CATEGORIES.find((c) => c.value === value)?.label || value

export function formatDate(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  return d.toLocaleDateString('en-ZA', { day: 'numeric', month: 'short', year: 'numeric' })
}

export function formatDateTime(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  return `${formatDate(iso)} — ${d.toLocaleTimeString('en-ZA', {
    hour: '2-digit',
    minute: '2-digit',
  })}`
}
