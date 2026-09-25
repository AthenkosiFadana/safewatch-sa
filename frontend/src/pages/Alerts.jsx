import { useEffect, useState } from 'react'
import api from '../services/api'
import AlertCard, { EmptyAlerts } from '../components/AlertCard'

export default function Alerts() {
  const [alerts, setAlerts] = useState([])
  const [error, setError] = useState('')

  useEffect(() => {
    api.listAlerts().then((d) => setAlerts(d.alerts)).catch((e) => setError(e.message))
  }, [])

  return (
    <div className="mx-auto max-w-3xl px-4 py-8">
      <div className="flex items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Community safety alerts</h1>
          <p className="text-sm text-slate-500">
            Automatically raised when 3+ incidents hit one area within 2 hours. Notifications are
            published through Amazon SNS in AWS.
          </p>
        </div>
        <button
          onClick={() => api.checkAlerts().then(() => api.listAlerts()).then((d) => setAlerts(d.alerts)).catch((e) => setError(e.message))}
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
        >
          Run detection
        </button>
      </div>

      {error && <p className="mt-4 rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</p>}

      <div className="mt-6 flex flex-col gap-4">
        {alerts.length ? alerts.map((a) => <AlertCard key={a.alertId} alert={a} />) : <EmptyAlerts />}
      </div>
    </div>
  )
}
