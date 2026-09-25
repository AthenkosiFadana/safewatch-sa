import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { AREAS } from '../constants'

export default function Register() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ name: '', email: '', password: '', community: '' })
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function submit(e) {
    e.preventDefault()
    setError('')
    setBusy(true)
    try {
      await register(form)
      navigate('/dashboard')
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  const set = (key) => (e) => setForm({ ...form, [key]: e.target.value })

  return (
    <div className="mx-auto max-w-md px-4 py-12">
      <div className="rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
        <h1 className="text-2xl font-bold text-slate-900">Create your account</h1>
        <p className="mt-1 text-sm text-slate-500">Join your community safety network.</p>

        {error && (
          <p className="mt-4 rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</p>
        )}

        <form onSubmit={submit} className="mt-6 flex flex-col gap-4">
          <label className="block text-sm font-medium text-slate-700">
            Full name
            <input required value={form.name} onChange={set('name')} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 focus:border-slate-900 focus:outline-none" />
          </label>
          <label className="block text-sm font-medium text-slate-700">
            Email
            <input type="email" required value={form.email} onChange={set('email')} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 focus:border-slate-900 focus:outline-none" />
          </label>
          <label className="block text-sm font-medium text-slate-700">
            Password <span className="font-normal text-slate-400">(min 8 characters)</span>
            <input type="password" required minLength={8} value={form.password} onChange={set('password')} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 focus:border-slate-900 focus:outline-none" />
          </label>
          <label className="block text-sm font-medium text-slate-700">
            Community / area
            <select value={form.community} onChange={set('community')} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 focus:border-slate-900 focus:outline-none">
              <option value="">Select your area</option>
              {AREAS.map((a) => <option key={a} value={a}>{a}</option>)}
            </select>
          </label>
          <button disabled={busy} className="rounded-lg bg-slate-900 px-4 py-2.5 font-semibold text-white hover:bg-slate-700 disabled:opacity-60">
            {busy ? 'Creating account…' : 'Register'}
          </button>
        </form>

        <p className="mt-4 text-sm text-slate-500">
          Already registered?{' '}
          <Link to="/login" className="font-semibold text-red-600 hover:underline">Login</Link>
        </p>
      </div>
    </div>
  )
}
