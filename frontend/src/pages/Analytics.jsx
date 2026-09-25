import { useEffect, useState } from 'react'
import {
  Bar, BarChart, CartesianGrid, Cell, Legend, Line, LineChart, Pie, PieChart,
  ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts'
import api from '../services/api'
import DashboardCard from '../components/DashboardCard'
import { SEVERITY_META } from '../constants'

const COLORS = ['#dc2626', '#f97316', '#eab308', '#16a34a', '#0ea5e9', '#8b5cf6', '#64748b', '#db2777', '#14b8a6']

export default function Analytics() {
  const [data, setData] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    api.analytics().then(setData).catch((e) => setError(e.message))
  }, [])

  if (error) return <div className="mx-auto max-w-7xl px-4 py-8 text-rose-600">{error}</div>
  if (!data) return <div className="mx-auto max-w-7xl px-4 py-8 text-slate-500">Loading analytics…</div>

  const severityData = data.bySeverity.map((s) => ({ ...s, name: s.key, value: s.count }))

  return (
    <div className="mx-auto max-w-7xl px-4 py-8">
      <h1 className="text-2xl font-bold text-slate-900">Crime analytics</h1>
      <p className="text-sm text-slate-500">
        Aggregated from SafeWatch reports. Community, official (SAPS) and demo datasets are tagged
        separately with a <code className="rounded bg-slate-100 px-1">source</code> field.
      </p>

      <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <DashboardCard title="Total incidents" value={data.total} icon="📊" />
        <DashboardCard title="Top category" value={data.byCategory[0]?.key?.replace('_', ' ') || '—'} icon="🗂️" accent="text-red-600" />
        <DashboardCard title="Top hotspot" value={data.hotspots[0]?.area || '—'} icon="📍" accent="text-orange-600" />
        <DashboardCard title="Busiest time block" value={data.timeBuckets.reduce((a, b) => (a.count > b.count ? a : b)).label} icon="🕒" accent="text-blue-600" />
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <Card title="Incidents by category">
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={data.byCategory.map((c) => ({ name: c.key.replace('_', ' '), count: c.count }))}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" tick={{ fontSize: 11 }} interval={0} angle={-20} textAnchor="end" height={60} />
              <YAxis />
              <Tooltip />
              <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                {data.byCategory.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Card>

        <Card title="Severity split">
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie data={severityData} dataKey="value" nameKey="name" innerRadius={60} outerRadius={100} label>
                {severityData.map((s) => (
                  <Cell key={s.key} fill={SEVERITY_META[s.key]?.color || '#64748b'} />
                ))}
              </Pie>
              <Legend />
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </Card>

        <Card title="Incidents by time of day">
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={data.timeBuckets.map((t) => ({ name: t.label, count: t.count }))}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" tick={{ fontSize: 11 }} />
              <YAxis />
              <Tooltip />
              <Bar dataKey="count" fill="#dc2626" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
          <ul className="mt-2 space-y-1 text-sm text-slate-600">
            {data.timeBuckets.map((t) => (
              <li key={t.label} className="flex justify-between">
                <span>{t.label}</span>
                <span className="font-semibold">{t.percent}%</span>
              </li>
            ))}
          </ul>
        </Card>

        <Card title="Crime hotspots by area">
          <ul className="space-y-3">
            {data.hotspots.map((h) => (
              <li key={h.area}>
                <div className="flex justify-between text-sm text-slate-700">
                  <span>{h.area}</span>
                  <span className="font-semibold">{h.count}</span>
                </div>
                <div className="mt-1 h-2.5 rounded-full bg-slate-100">
                  <div
                    className="h-2.5 rounded-full bg-gradient-to-r from-orange-500 to-red-600"
                    style={{ width: `${(h.count / (data.hotspots[0]?.count || 1)) * 100}%` }}
                  />
                </div>
              </li>
            ))}
          </ul>
        </Card>

        <Card title="Incidents over the last 7 days" wide>
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={data.trend}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="day" tick={{ fontSize: 11 }} />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Line type="monotone" dataKey="count" stroke="#dc2626" strokeWidth={2.5} dot={{ r: 4 }} />
            </LineChart>
          </ResponsiveContainer>
        </Card>
      </div>
    </div>
  )
}

function Card({ title, children, wide }) {
  return (
    <div className={`rounded-xl border border-slate-200 bg-white p-5 shadow-sm ${wide ? 'lg:col-span-2' : ''}`}>
      <h2 className="mb-4 font-bold text-slate-900">{title}</h2>
      {children}
    </div>
  )
}
