import { useEffect, useMemo, useState } from 'react'
import api from '../services/api'
import IncidentMap from '../components/IncidentMap'
import IncidentCard from '../components/IncidentCard'
import { AREAS, CATEGORIES, SEVERITIES } from '../constants'

export default function MapPage() {
  const [incidents, setIncidents] = useState([])
  const [filters, setFilters] = useState({ category: '', severity: '', area: '' })
  const [selected, setSelected] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    api.listIncidents().then((d) => setIncidents(d.incidents)).catch((e) => setError(e.message))
  }, [])

  const filtered = useMemo(
    () =>
      incidents.filter(
        (i) =>
          (!filters.category || i.category === filters.category) &&
          (!filters.severity || i.severity === filters.severity) &&
          (!filters.area || i.area === filters.area) &&
          i.status !== 'REJECTED'
      ),
    [incidents, filters]
  )

  const select = (incident) => {
    setSelected(incident)
    document.getElementById('incident-list')?.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-8">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Interactive crime map</h1>
          <p className="text-sm text-slate-500">
            🟢 Low · 🟡 Medium · 🟠 High · 🔴 Critical — click a marker for details
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <select value={filters.category} onChange={(e) => setFilters({ ...filters, category: e.target.value })} className="rounded-lg border border-slate-300 px-3 py-2 text-sm">
            <option value="">All categories</option>
            {CATEGORIES.map((c) => <option key={c.value} value={c.value}>{c.label}</option>)}
          </select>
          <select value={filters.severity} onChange={(e) => setFilters({ ...filters, severity: e.target.value })} className="rounded-lg border border-slate-300 px-3 py-2 text-sm">
            <option value="">All severities</option>
            {SEVERITIES.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
          <select value={filters.area} onChange={(e) => setFilters({ ...filters, area: e.target.value })} className="rounded-lg border border-slate-300 px-3 py-2 text-sm">
            <option value="">All areas</option>
            {AREAS.map((a) => <option key={a} value={a}>{a}</option>)}
          </select>
        </div>
      </div>

      {error && <p className="mt-4 rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</p>}

      <div className="mt-5 grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <IncidentMap incidents={filtered} selectedId={selected?.incidentId} onSelect={select} height="h-[560px]" />
          <p className="mt-2 text-xs text-slate-400">{filtered.length} incidents shown</p>
        </div>
        <div id="incident-list" className="flex max-h-[560px] flex-col gap-3 overflow-y-auto pr-1">
          {selected && (
            <div className="rounded-xl border-2 border-red-500 bg-white p-3">
              <p className="text-xs font-semibold uppercase text-red-600">Selected incident</p>
              <IncidentCard incident={selected} />
            </div>
          )}
          {filtered.slice(0, 30).map((i) => (
            <IncidentCard key={i.incidentId} incident={i} />
          ))}
          {!filtered.length && <p className="text-sm text-slate-500">No incidents match these filters.</p>}
        </div>
      </div>
    </div>
  )
}
