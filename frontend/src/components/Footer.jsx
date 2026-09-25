import { Link } from 'react-router-dom'

export default function Footer() {
  return (
    <footer className="mt-12 border-t border-slate-200 bg-white">
      <div className="mx-auto grid max-w-7xl gap-6 px-4 py-8 text-sm text-slate-500 sm:grid-cols-3">
        <div>
          <p className="font-semibold text-slate-800">🇿🇦 SafeWatch SA</p>
          <p className="mt-1">See it. Report it. Stay informed.</p>
        </div>
        <div>
          <p className="font-semibold text-slate-800">In an emergency</p>
          <p className="mt-1">
            Call <strong className="text-red-600">10111</strong> or visit your nearest SAPS police
            station. SafeWatch SA is a community information platform and does not replace SAPS.
          </p>
        </div>
        <div className="flex flex-col gap-1">
          <Link to="/report" className="hover:text-slate-800">Report an incident</Link>
          <Link to="/map" className="hover:text-slate-800">Incident map</Link>
          <Link to="/analytics" className="hover:text-slate-800">Crime analytics</Link>
        </div>
      </div>
      <div className="border-t border-slate-100 px-4 py-4 text-center text-xs text-slate-400">
        Demo/portfolio project. Data shown may be synthetic (source=DEMO) and is not official SAPS
        crime statistics.
      </div>
    </footer>
  )
}
