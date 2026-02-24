import { useEffect, useMemo, useState } from 'react'
import { api, getApiBase, setApiBase } from './api'

const tabs = ['dashboard', 'robots', 'orders', 'tasks', 'allocator', 'telemetry']

function Badge({ value }) {
  if (!value) return '-'
  return <span className={`badge ${value}`}>{value}</span>
}

function Panel({ title, children, actions }) {
  return (
    <section className="card">
      <div className="panel-head">
        <h3>{title}</h3>
        <div>{actions}</div>
      </div>
      {children}
    </section>
  )
}

export default function App() {
  const [tab, setTab] = useState((location.hash || '#/dashboard').replace('#/', ''))
  const [apiBase, setApiBaseInput] = useState(getApiBase())
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const [dashboard, setDashboard] = useState({ summary: null, fleet: [] })
  const [robots, setRobots] = useState([])
  const [robotDetail, setRobotDetail] = useState(null)
  const [orders, setOrders] = useState([])
  const [tasks, setTasks] = useState([])
  const [telemetryLatest, setTelemetryLatest] = useState([])
  const [allocResult, setAllocResult] = useState(null)

  useEffect(() => {
    const onHash = () => setTab((location.hash || '#/dashboard').replace('#/', ''))
    window.addEventListener('hashchange', onHash)
    return () => window.removeEventListener('hashchange', onHash)
  }, [])

  const summaryMap = useMemo(() => {
    const s = dashboard.summary
    if (!s) return {}
    return {
      robots: (s.robots_by_status || []).map((x) => `${x.key}:${x.count}`).join(' | '),
      orders: (s.orders_by_status || []).map((x) => `${x.key}:${x.count}`).join(' | '),
      tasks: (s.tasks_by_status || []).map((x) => `${x.key}:${x.count}`).join(' | '),
    }
  }, [dashboard.summary])

  async function loadDashboard() {
    const [summary, fleet] = await Promise.all([api('/dashboard/summary'), api('/dashboard/fleet')])
    setDashboard({ summary, fleet })
  }

  async function loadRobots() {
    setRobots(await api('/robots'))
  }

  async function loadOrders() {
    setOrders(await api('/orders'))
  }

  async function loadTasks() {
    setTasks(await api('/tasks'))
  }

  async function loadTelemetry() {
    setTelemetryLatest(await api('/telemetry/latest'))
  }

  async function refreshCurrent() {
    setLoading(true)
    setError('')
    try {
      if (tab === 'dashboard') await loadDashboard()
      if (tab === 'robots') await loadRobots()
      if (tab === 'orders') await loadOrders()
      if (tab === 'tasks') await loadTasks()
      if (tab === 'telemetry') await loadTelemetry()
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    refreshCurrent()
  }, [tab])

  async function withAction(fn) {
    setLoading(true)
    setError('')
    try {
      await fn()
      await refreshCurrent()
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  function formatTime(ts) {
    return ts ? new Date(ts).toLocaleString() : '-'
  }

  return (
    <div>
      <header className="topbar">
        <div>
          <h1>Mini WES</h1>
          <p className="muted">React + Vite frontend</p>
        </div>
        <form
          className="inline"
          onSubmit={(e) => {
            e.preventDefault()
            setApiBase(apiBase)
            refreshCurrent()
          }}
        >
          <input value={apiBase} onChange={(e) => setApiBaseInput(e.target.value)} placeholder="http://127.0.0.1:8000" />
          <button type="submit">Save API</button>
        </form>
      </header>

      <nav className="tabs">
        {tabs.map((t) => (
          <a key={t} href={`#/${t}`} className={tab === t ? 'active' : ''}>
            {t[0].toUpperCase() + t.slice(1)}
          </a>
        ))}
      </nav>

      <main className="content">
        {error ? <section className="card error">{error}</section> : null}
        {loading ? <section className="card">Loading...</section> : null}

        {tab === 'dashboard' && dashboard.summary ? (
          <>
            <Panel title="Summary" actions={<button onClick={refreshCurrent}>Refresh</button>}>
              <p><b>Robots Total:</b> {dashboard.summary.robots_total}</p>
              <p><b>Tasks Running:</b> {dashboard.summary.tasks_running}</p>
              <p className="muted">Robots: {summaryMap.robots}</p>
              <p className="muted">Orders: {summaryMap.orders}</p>
              <p className="muted">Tasks: {summaryMap.tasks}</p>
            </Panel>
            <Panel title="Fleet">
              <table>
                <thead><tr><th>Robot</th><th>Status</th><th>Battery</th><th>Pose</th><th>Task</th></tr></thead>
                <tbody>
                  {dashboard.fleet.map((r) => (
                    <tr key={r.robot_id}>
                      <td>{r.name}</td>
                      <td><Badge value={r.status} /></td>
                      <td>{r.battery_pct}%</td>
                      <td>{r.x?.toFixed(2)}, {r.y?.toFixed(2)}</td>
                      <td>{r.active_task_code || '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Panel>
          </>
        ) : null}

        {tab === 'robots' ? (
          <>
            <Panel title="Register Robot">
              <form
                className="inline"
                onSubmit={(e) => {
                  e.preventDefault()
                  const fd = new FormData(e.currentTarget)
                  withAction(async () => {
                    await api('/robots', {
                      method: 'POST',
                      body: JSON.stringify({
                        name: fd.get('name'),
                        robot_type: fd.get('robot_type'),
                        battery_pct: Number(fd.get('battery_pct') || 100),
                        status: 'IDLE',
                      }),
                    })
                    e.currentTarget.reset()
                  })
                }}
              >
                <input name="name" placeholder="AMR-01" required />
                <input name="robot_type" placeholder="AMR" required />
                <input name="battery_pct" type="number" min="0" max="100" defaultValue="100" required />
                <button type="submit">Create</button>
              </form>
            </Panel>

            <Panel title="Robots" actions={<button onClick={refreshCurrent}>Refresh</button>}>
              <table>
                <thead><tr><th>Name</th><th>Type</th><th>Status</th><th>Battery</th><th>Actions</th></tr></thead>
                <tbody>
                  {robots.map((r) => (
                    <tr key={r.id}>
                      <td>{r.name}</td>
                      <td>{r.robot_type}</td>
                      <td><Badge value={r.status} /></td>
                      <td>{r.battery_pct}%</td>
                      <td>
                        <button className="secondary" onClick={() => withAction(async () => setRobotDetail(await api(`/robots/${r.id}`)))}>Detail</button>
                        <button className="secondary" onClick={() => withAction(() => api(`/robots/${r.id}`, { method: 'PATCH', body: JSON.stringify({ enabled: true }) }))}>Enable</button>
                        <button className="danger" onClick={() => withAction(() => api(`/robots/${r.id}`, { method: 'PATCH', body: JSON.stringify({ enabled: false }) }))}>Disable</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Panel>

            <Panel title="Robot Detail">
              {robotDetail ? (
                <div>
                  <p><b>{robotDetail.name}</b> ({robotDetail.robot_type})</p>
                  <p>Status: <Badge value={robotDetail.status} /> | Battery: {robotDetail.battery_pct}%</p>
                  <p>Pose: {robotDetail.last_pose_x?.toFixed(2)}, {robotDetail.last_pose_y?.toFixed(2)}</p>
                </div>
              ) : <p className="muted">Click Detail on a robot</p>}
            </Panel>
          </>
        ) : null}

        {tab === 'orders' ? (
          <>
            <Panel title="Create Order">
              <form
                className="inline"
                onSubmit={(e) => {
                  e.preventDefault()
                  const fd = new FormData(e.currentTarget)
                  withAction(async () => {
                    await api('/orders', {
                      method: 'POST',
                      body: JSON.stringify({
                        code: fd.get('code') || null,
                        priority: Number(fd.get('priority') || 5),
                        pickup_location: { x: Number(fd.get('px')), y: Number(fd.get('py')) },
                        dropoff_location: { x: Number(fd.get('dx')), y: Number(fd.get('dy')) },
                      }),
                    })
                    e.currentTarget.reset()
                  })
                }}
              >
                <input name="code" placeholder="optional code" />
                <input name="px" type="number" step="0.1" placeholder="pickup x" required />
                <input name="py" type="number" step="0.1" placeholder="pickup y" required />
                <input name="dx" type="number" step="0.1" placeholder="dropoff x" required />
                <input name="dy" type="number" step="0.1" placeholder="dropoff y" required />
                <input name="priority" type="number" min="1" max="10" defaultValue="5" required />
                <button type="submit">Create</button>
              </form>
            </Panel>

            <Panel title="Orders" actions={<button onClick={refreshCurrent}>Refresh</button>}>
              <table>
                <thead><tr><th>Code</th><th>Status</th><th>Priority</th><th>Actions</th></tr></thead>
                <tbody>
                  {orders.map((o) => (
                    <tr key={o.id}>
                      <td>{o.code}</td>
                      <td><Badge value={o.status} /></td>
                      <td>{o.priority}</td>
                      <td>
                        <button className="secondary" onClick={() => withAction(() => api(`/orders/${o.id}`, { method: 'PATCH', body: JSON.stringify({ priority: 1 }) }))}>Set P1</button>
                        <button className="danger" onClick={() => withAction(() => api(`/orders/${o.id}`, { method: 'PATCH', body: JSON.stringify({ status: 'CANCELED' }) }))}>Cancel</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Panel>
          </>
        ) : null}

        {tab === 'tasks' ? (
          <Panel title="Tasks" actions={<button onClick={refreshCurrent}>Refresh</button>}>
            <table>
              <thead><tr><th>Code</th><th>Status</th><th>Robot</th><th>Order</th><th>Progress</th><th>Started</th></tr></thead>
              <tbody>
                {tasks.map((t) => (
                  <tr key={t.id}>
                    <td>{t.code}</td>
                    <td><Badge value={t.status} /></td>
                    <td>{t.assigned_robot_id || '-'}</td>
                    <td>{t.order_id || '-'}</td>
                    <td>{t.progress_pct}%</td>
                    <td>{formatTime(t.started_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Panel>
        ) : null}

        {tab === 'allocator' ? (
          <>
            <Panel title="Run Allocation">
              <form
                className="inline"
                onSubmit={(e) => {
                  e.preventDefault()
                  const fd = new FormData(e.currentTarget)
                  withAction(async () => {
                    const data = await api('/allocator/run', {
                      method: 'POST',
                      body: JSON.stringify({
                        max_orders: Number(fd.get('max_orders') || 20),
                        battery_min_pct: Number(fd.get('battery_min_pct') || 20),
                      }),
                    })
                    setAllocResult(data)
                  })
                }}
              >
                <input name="max_orders" type="number" min="1" max="200" defaultValue="20" />
                <input name="battery_min_pct" type="number" min="0" max="100" defaultValue="20" />
                <button type="submit">Run</button>
              </form>
            </Panel>
            <Panel title="Result">
              {allocResult ? <pre>{JSON.stringify(allocResult, null, 2)}</pre> : <p className="muted">No run yet</p>}
            </Panel>
          </>
        ) : null}

        {tab === 'telemetry' ? (
          <>
            <Panel title="Ingest Telemetry">
              <form
                className="inline"
                onSubmit={(e) => {
                  e.preventDefault()
                  const fd = new FormData(e.currentTarget)
                  withAction(async () => {
                    await api('/telemetry/ingest', {
                      method: 'POST',
                      body: JSON.stringify({
                        robot_id: fd.get('robot_id'),
                        x: Number(fd.get('x')),
                        y: Number(fd.get('y')),
                        theta: Number(fd.get('theta') || 0),
                        battery_pct: Number(fd.get('battery_pct')),
                      }),
                    })
                  })
                }}
              >
                <input name="robot_id" placeholder="robot uuid" required />
                <input name="x" type="number" step="0.1" placeholder="x" required />
                <input name="y" type="number" step="0.1" placeholder="y" required />
                <input name="theta" type="number" step="0.1" placeholder="theta" defaultValue="0" />
                <input name="battery_pct" type="number" min="0" max="100" placeholder="battery" required />
                <button type="submit">Send</button>
                <a className="button-link" href={`${getApiBase()}/telemetry/export.csv`} target="_blank" rel="noreferrer">Download CSV</a>
              </form>
            </Panel>

            <Panel title="Latest Telemetry" actions={<button onClick={refreshCurrent}>Refresh</button>}>
              <table>
                <thead><tr><th>Robot</th><th>x</th><th>y</th><th>theta</th><th>battery</th><th>recorded_at</th></tr></thead>
                <tbody>
                  {telemetryLatest.map((x) => (
                    <tr key={`${x.robot_id}-${x.recorded_at}`}>
                      <td>{x.robot_id}</td>
                      <td>{x.x?.toFixed(2)}</td>
                      <td>{x.y?.toFixed(2)}</td>
                      <td>{x.theta?.toFixed(2)}</td>
                      <td>{x.battery_pct}%</td>
                      <td>{formatTime(x.recorded_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Panel>
          </>
        ) : null}
      </main>
    </div>
  )
}
