import { useState } from 'react'
import api from '../services/api'
import { useAuth } from '../context/AuthContext'
import { AREAS } from '../constants'

export default function Profile() {
  const { user, refreshUser } = useAuth()
  const [form, setForm] = useState({
    name: user?.name || '',
    community: user?.community || '',
    password: '',
  })
  const [message, setMessage] = useState(null)

  async function submit(e) {
    e.preventDefault()
    try {
      const payload = { name: form.name, community: form.community }
      if (form.password) payload.password = form.password
      await api.updateProfile(payload)
      await refreshUser()
      setMessage({ ok: true, text: 'Profile updated' })
      setForm({ ...form, password: '' })
    } catch (err) {
      setMessage({ ok: false, text: err.message })
    }
  }

  if (!user) return null

  return (
    <div className="mx-auto max-w-lg px-4 py-10">
      <h1 className="text-2xl font-bold text-slate-900">My profile</h1>
      <p className="mt-1 text-sm text-slate-500">
        {user.email} · Role: <strong>{user.role}</strong>
      </p>

      {message && (
        <p className={`mt-4 rounded-lg px-3 py-2 text-sm ${message.ok ? 'bg-emerald-50 text-emerald-700' : 'bg-rose-50 text-rose-700'}`}>
          {message.text}
        </p>
      )}

      <form onSubmit={submit} className="mt-6 flex flex-col gap-4 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <label className="block text-sm font-medium text-slate-700">
          Full name
          <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2" />
        </label>
        <label className="block text-sm font-medium text-slate-700">
          Community / area
          <select value={form.community} onChange={(e) => setForm({ ...form, community: e.target.value })} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2">
            <option value="">Not set</option>
            {AREAS.map((a) => <option key={a} value={a}>{a}</option>)}
          </select>
        </label>
        <label className="block text-sm font-medium text-slate-700">
          New password <span className="font-normal text-slate-400">(leave blank to keep current)</span>
          <input type="password" minLength={8} value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2" />
        </label>
        <button className="rounded-lg bg-slate-900 px-4 py-2.5 font-semibold text-white hover:bg-slate-700">Save changes</button>
      </form>
    </div>
  )
}
