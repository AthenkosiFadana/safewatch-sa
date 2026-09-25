export default function DashboardCard({ title, value, icon, accent = 'text-slate-900', hint }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium text-slate-500">{title}</p>
        {icon && <span className="text-xl">{icon}</span>}
      </div>
      <p className={`mt-2 text-3xl font-bold ${accent}`}>{value}</p>
      {hint && <p className="mt-1 text-xs text-slate-400">{hint}</p>}
    </div>
  )
}
