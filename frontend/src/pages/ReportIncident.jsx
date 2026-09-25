import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../services/api'
import { AREAS, CATEGORIES, SEVERITIES } from '../constants'

const DEFAULTS = { lat: -33.9614, lon: 25.6022 }

export default function ReportIncident() {
  const navigate = useNavigate()
  const [form, setForm] = useState({
    category: 'THEFT',
    area: AREAS[0],
    description: '',
    severity: 'MEDIUM',
    latitude: DEFAULTS.lat,
    longitude: DEFAULTS.lon,
  })
  const [errors, setErrors] = useState([])
  const [busy, setBusy] = useState(false)
  const [result, setResult] = useState(null)

  const set = (key) => (e) => setForm({ ...form, [key]: e.target.value })

  function useMyLocation() {
    if (!navigator.geolocation) return
    navigator.geolocation.getCurrentPosition(
      (pos) => setForm((f) => ({ ...f, latitude: +pos.coords.latitude.toFixed(6), longitude: +pos.coords.longitude.toFixed(6) })),
      () => setErrors(['Could not read your location — enter coordinates manually'])
    )
  }

  async function submit(e) {
    e.preventDefault()
    setErrors([])
    setBusy(true)
    try {
      const data = await api.createIncident({
        ...form,
        latitude: Number(form.latitude),
        longitude: Number(form.longitude),
      })
      setResult(data)
    } catch (err) {
      setErrors([err.message])
    } finally {
      setBusy(false)
    }
  }

  if (result) {
    return (
      <div className="mx-auto max-w-xl px-4 py-12">
        <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-8 text-center">
          <p className="text-4xl">✅</p>
          <h1 className="mt-3 text-xl font-bold text-emerald-900">Report submitted</h1>
          <p className="mt-2 text-sm text-emerald-800">
            Incident <strong>{result.incident.incidentId}</strong> was recorded with status{' '}
            <strong>PENDING</strong> and will be reviewed by moderators.
          </p>
          {result.flaggedDuplicates?.length > 0 && (
            <p className="mt-3 rounded bg-amber-100 px-3 py-2 text-xs text-amber-800">
              Flagged as possibly related to: {result.flaggedDuplicates.join(', ')}
            </p>
          )}
          <div className="mt-6 flex justify-center gap-3">
            <button onClick={() => navigate(`/incidents/${result.incident.incidentId}`)} className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white">
              View report
            </button>
            <button onClick={() => { setResult(null); setForm({ ...form, description: '' }) }} className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-semibold">
              Report another
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-xl px-4 py-10">
      <h1 className="text-2xl font-bold text-slate-900">Report an incident</h1>
      <p className="mt-1 text-sm text-slate-500">
        Reports are moderated before they are verified. In an emergency call 10111.
      </p>

      {errors.length > 0 && (
        <div className="mt-4 rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">
          {errors.map((e) => <p key={e}>{e}</p>)}
        </div>
      )}

      <form onSubmit={submit} className="mt-6 flex flex-col gap-4 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <label className="block text-sm font-medium text-slate-700">
          Incident Type
          <select value={form.category} onChange={set('category')} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2">
            {CATEGORIES.map((c) => <option key={c.value} value={c.value}>{c.label}</option>)}
          </select>
        </label>

        <label className="block text-sm font-medium text-slate-700">
          Location (area)
          <select value={form.area} onChange={set('area')} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2">
            {AREAS.map((a) => <option key={a} value={a}>{a}</option>)}
          </select>
        </label>

        <label className="block text-sm font-medium text-slate-700">
          Description
          <textarea
            required
            minLength={10}
            rows={4}
            value={form.description}
            onChange={set('description')}
            placeholder="Vehicle break-in reported near…"
            className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 focus:border-slate-900 focus:outline-none"
          />
        </label>

        <div className="grid grid-cols-2 gap-3">
          <label className="block text-sm font-medium text-slate-700">
            Latitude
            <input required value={form.latitude} onChange={set('latitude')} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2" />
          </label>
          <label className="block text-sm font-medium text-slate-700">
            Longitude
            <input required value={form.longitude} onChange={set('longitude')} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2" />
          </label>
        </div>
        <button type="button" onClick={useMyLocation} className="self-start text-sm font-semibold text-red-600 hover:underline">
          📍 Use my current location
        </button>

        <label className="block text-sm font-medium text-slate-700">
          Severity
          <div className="mt-1 flex gap-2">
            {SEVERITIES.map((s) => (
              <button
                type="button"
                key={s}
                onClick={() => setForm({ ...form, severity: s })}
                className={`flex-1 rounded-lg border px-2 py-2 text-xs font-semibold ${
                  form.severity === s
                    ? 'border-slate-900 bg-slate-900 text-white'
                    : 'border-slate-300 text-slate-600 hover:bg-slate-50'
                }`}
              >
                {s}
              </button>
            ))}
          </div>
        </label>

        <label className="block text-sm font-medium text-slate-700">
          Date
          <input type="date" readOnly value={new Date().toISOString().slice(0, 10)} className="mt-1 w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-slate-500" />
        </label>

        <button disabled={busy} className="rounded-lg bg-red-600 px-4 py-3 font-semibold text-white hover:bg-red-700 disabled:opacity-60">
          {busy ? 'Submitting…' : 'SUBMIT REPORT'}
        </button>
      </form>
    </div>
  )
}
