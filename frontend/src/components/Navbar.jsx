import { Link, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Navbar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const linkClass = ({ isActive }) =>
    `px-3 py-2 rounded-lg text-sm font-medium transition ${
      isActive ? 'bg-slate-900 text-white' : 'text-slate-600 hover:bg-slate-100'
    }`

  return (
    <header className="sticky top-0 z-[1000] border-b border-slate-200 bg-white/95 backdrop-blur">
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-3">
        <Link to="/" className="flex items-center gap-2 text-lg font-bold text-slate-900">
          <span aria-hidden>🇿🇦</span> SafeWatch <span className="text-red-600">SA</span>
        </Link>

        <nav className="hidden items-center gap-1 md:flex">
          <NavLink to="/" end className={linkClass}>Home</NavLink>
          <NavLink to="/dashboard" className={linkClass}>Dashboard</NavLink>
          <NavLink to="/map" className={linkClass}>Map</NavLink>
          <NavLink to="/alerts" className={linkClass}>Alerts</NavLink>
          <NavLink to="/analytics" className={linkClass}>Analytics</NavLink>
          {user?.role === 'ADMIN' && <NavLink to="/admin" className={linkClass}>Admin</NavLink>}
        </nav>

        <div className="flex items-center gap-2">
          {user ? (
            <>
              <Link
                to="/report"
                className="hidden rounded-lg bg-red-600 px-3 py-2 text-sm font-semibold text-white hover:bg-red-700 sm:block"
              >
                Report Incident
              </Link>
              <Link to="/profile" className="hidden text-sm font-medium text-slate-700 hover:text-slate-900 sm:block">
                {user.name.split(' ')[0]}
              </Link>
              <button
                onClick={() => {
                  logout()
                  navigate('/')
                }}
                className="rounded-lg border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
              >
                Logout
              </button>
            </>
          ) : (
            <>
              <Link to="/login" className="rounded-lg border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50">
                Login
              </Link>
              <Link to="/register" className="rounded-lg bg-slate-900 px-3 py-2 text-sm font-semibold text-white hover:bg-slate-700">
                Register
              </Link>
            </>
          )}
        </div>
      </div>

      <nav className="flex gap-1 overflow-x-auto border-t border-slate-100 px-3 py-2 md:hidden">
        <NavLink to="/" end className={linkClass}>Home</NavLink>
        <NavLink to="/dashboard" className={linkClass}>Dashboard</NavLink>
        <NavLink to="/map" className={linkClass}>Map</NavLink>
        <NavLink to="/alerts" className={linkClass}>Alerts</NavLink>
        <NavLink to="/analytics" className={linkClass}>Analytics</NavLink>
        <NavLink to="/report" className={linkClass}>Report</NavLink>
        {user?.role === 'ADMIN' && <NavLink to="/admin" className={linkClass}>Admin</NavLink>}
      </nav>
    </header>
  )
}
