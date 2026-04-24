import { useEffect, useMemo, useState } from 'react'
import { createTicket, fetchDashboard, fetchTickets, login, updateTicket } from './api'

const departments = [
  'Engineering',
  'Finance',
  'HR',
  'Operations',
  'Sales',
  'Marketing',
  'Executive',
  'Customer Support',
  'Product Management',
  'Legal',
  'Procurement',
  'Facilities',
  'Data Analytics',
  'IT Service Desk',
  'IT Operations',
  'Network & VPN',
  'Security Operations',
  'Identity & Access',
  'Endpoint Support',
  'Business Applications',
]

const employeeTemplate = {
  role: 'employee',
  name: '',
  email: '',
  department: 'Engineering',
}

const adminTemplate = {
  role: 'admin',
  name: '',
  email: '',
  department: 'IT Operations',
}

const ticketViewerTemplate = {
  role: 'employee',
  name: '',
  email: '',
  department: 'Employee',
}

const ticketTemplate = {
  title: '',
  description: '',
}

export default function App() {
  const [roleChoice, setRoleChoice] = useState('employee')
  const [session, setSession] = useState(() => {
    const saved = localStorage.getItem('helpdesk-session')
    return saved ? JSON.parse(saved) : null
  })
  const [loginForm, setLoginForm] = useState(employeeTemplate)
  const [ticketForm, setTicketForm] = useState(ticketTemplate)
  const [tickets, setTickets] = useState([])
  const [dashboard, setDashboard] = useState(null)
  const [adminDrafts, setAdminDrafts] = useState({})
  const [latestAnalysis, setLatestAnalysis] = useState(null)
  const [successMessage, setSuccessMessage] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    localStorage.setItem('helpdesk-session', JSON.stringify(session))
  }, [session])

  useEffect(() => {
    if (roleChoice === 'admin') {
      setLoginForm(adminTemplate)
    } else if (roleChoice === 'ticket_viewer') {
      setLoginForm(ticketViewerTemplate)
    } else {
      setLoginForm(employeeTemplate)
    }
    setError('')
    setSuccessMessage('')
  }, [roleChoice])

  useEffect(() => {
    if (!session) return
    refreshData(session)
  }, [session])

  async function refreshData(activeSession = session) {
    if (!activeSession) return
    try {
      setError('')
      const ticketPromise = fetchTickets(
        activeSession.role,
        activeSession.role === 'employee' ? activeSession.email : undefined,
      )
      const dashboardPromise = activeSession.role === 'admin' ? fetchDashboard() : Promise.resolve(null)
      const [ticketData, dashboardData] = await Promise.all([ticketPromise, dashboardPromise])
      setTickets(ticketData)
      setDashboard(dashboardData)
      if (activeSession.role === 'employee' && ticketData.length > 0) {
        setLatestAnalysis(ticketData[0])
      }
    } catch (err) {
      setError(err.message)
    }
  }

  async function handleEmployeeIntake(event) {
    event.preventDefault()
    setBusy(true)
    setError('')
    setSuccessMessage('')
    try {
      const user = await login({ ...loginForm, role: 'employee' })
      const createdTicket = await createTicket({
        requester_name: user.name,
        requester_email: user.email,
        department: user.department,
        title: ticketForm.title,
        description: ticketForm.description,
      })
      setSession(user)
      setLatestAnalysis(createdTicket)
      setSuccessMessage(buildTicketStatusMessage(createdTicket))
      setTicketForm(ticketTemplate)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  async function handleAdminLogin(event) {
    event.preventDefault()
    setBusy(true)
    setError('')
    setSuccessMessage('')
    try {
      const user = await login({ ...loginForm, role: 'admin' })
      setSession(user)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  async function handleTicketViewerLogin(event) {
    event.preventDefault()
    setBusy(true)
    setError('')
    setSuccessMessage('')
    try {
      const user = await login({
        ...loginForm,
        role: 'employee',
        department: loginForm.department || 'Employee',
      })
      setSession({ ...user, accessMode: 'ticket_viewer' })
      setSuccessMessage(`Signed in to ticket tracker for ${user.email}.`)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  async function handleSubmitTicket(event) {
    event.preventDefault()
    setBusy(true)
    setError('')
    setSuccessMessage('')
    try {
      const createdTicket = await createTicket({
        requester_name: session.name,
        requester_email: session.email,
        department: session.department,
        title: ticketForm.title,
        description: ticketForm.description,
      })
      setLatestAnalysis(createdTicket)
      setSuccessMessage(buildTicketStatusMessage(createdTicket))
      setTicketForm(ticketTemplate)
      await refreshData()
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  async function handleAdminUpdate(ticketId, nextStatus) {
    const draft = adminDrafts[ticketId] || { admin_note: '' }
    setBusy(true)
    setError('')
    setSuccessMessage('')
    try {
      const updatedTicket = await updateTicket(ticketId, {
        status: nextStatus,
        admin_note: draft.admin_note,
        admin_name: session.name,
      })
      setTickets((current) => current.map((ticket) => (ticket.id === ticketId ? updatedTicket : ticket)))
      setAdminDrafts((current) => ({
        ...current,
        [ticketId]: {
          ...draft,
          status: nextStatus,
          admin_note: updatedTicket.admin_note,
        },
      }))
      setSuccessMessage(`Ticket ${updatedTicket.id} updated to ${prettyStatus(updatedTicket.status)} by ${session.name}.`)
      await refreshData()
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  function logout() {
    setSession(null)
    setTickets([])
    setDashboard(null)
    setAdminDrafts({})
    setLatestAnalysis(null)
    setSuccessMessage('')
    setError('')
  }

  const openCount = useMemo(() => tickets.filter((ticket) => !ticket.resolved).length, [tickets])
  const adminVisibleTickets = useMemo(
    () => tickets.filter((ticket) => ticket.status !== 'resolved'),
    [tickets],
  )

  if (!session) {
    return (
      <div className={`shell auth-shell ${roleChoice === 'ticket_viewer' ? 'centered-auth-shell' : 'simple-auth-shell'}`}>
        {roleChoice !== 'ticket_viewer' ? (
          <section className="auth-hero">
            <div className="auth-hero-copy">
              <p className="eyebrow">IT Helpdesk Workspace</p>
              <h1>One entrance for raising, tracking, and resolving support tickets.</h1>
              <p className="auth-lede">
                Designed for employees who need fast help and admins who need a clean queue. Pick the path that matches what you want to do.
              </p>
            </div>
            <div className="auth-feature-grid">
              <article className="auth-feature-card">
                <span className="feature-kicker">Raise Ticket</span>
                <strong>AI triage intake</strong>
                <p>Capture issue details and route them fast.</p>
              </article>
              <article className="auth-feature-card">
                <span className="feature-kicker">Check Ticket</span>
                <strong>Status tracker</strong>
                <p>Users can log in and view updates.</p>
              </article>
              <article className="auth-feature-card">
                <span className="feature-kicker">Admin Console</span>
                <strong>Active queue only</strong>
                <p>Resolve, progress, or mark unreachable.</p>
              </article>
            </div>
          </section>
        ) : null}

        <section className={`login-card intake-card full-span-card auth-panel ${roleChoice === 'ticket_viewer' ? 'auth-panel-wide' : ''}`}>
          <div className="auth-panel-top">
            <div>
              <p className="eyebrow">Portal Access</p>
              <h2>Select how you want to use the helpdesk</h2>
            </div>
            <span className="auth-status-pill">
              {roleChoice === 'employee' ? 'Raise Ticket' : roleChoice === 'ticket_viewer' ? 'Check Ticket' : 'Admin Login'}
            </span>
          </div>

          <div className="portal-switch">
            <button type="button" className={roleChoice === 'employee' ? 'active' : ''} onClick={() => setRoleChoice('employee')}>
              Raise Ticket
            </button>
            <button type="button" className={roleChoice === 'ticket_viewer' ? 'active' : ''} onClick={() => setRoleChoice('ticket_viewer')}>
              Check Ticket
            </button>
            <button type="button" className={roleChoice === 'admin' ? 'active' : ''} onClick={() => setRoleChoice('admin')}>
              Admin Login
            </button>
          </div>

          {roleChoice === 'employee' ? (
            <form className="ticket-form auth-form" onSubmit={handleEmployeeIntake}>
              <div>
                <p className="eyebrow">Raise A Ticket</p>
                <h2>Employee intake with ticket submission</h2>
              </div>
              <div className="form-split">
                <label>
                  Name
                  <input value={loginForm.name} onChange={(e) => setLoginForm({ ...loginForm, name: e.target.value })} required />
                </label>
                <label>
                  Email
                  <input type="email" value={loginForm.email} onChange={(e) => setLoginForm({ ...loginForm, email: e.target.value })} required />
                </label>
              </div>
              <label>
                Department
                <select value={loginForm.department} onChange={(e) => setLoginForm({ ...loginForm, department: e.target.value })}>
                  {departments.map((department) => (
                    <option key={department} value={department}>{department}</option>
                  ))}
                </select>
              </label>
              <label>
                Ticket title
                <input value={ticketForm.title} onChange={(e) => setTicketForm({ ...ticketForm, title: e.target.value })} required />
              </label>
              <label>
                Ticket description
                <textarea rows="7" value={ticketForm.description} onChange={(e) => setTicketForm({ ...ticketForm, description: e.target.value })} required />
              </label>
              {error ? <p className="error-banner">{error}</p> : null}
              <button className="primary-button" disabled={busy} type="submit">
                {busy ? 'Submitting ticket...' : 'Login And Raise Ticket'}
              </button>
            </form>
          ) : roleChoice === 'ticket_viewer' ? (
            <form className="ticket-form auth-form" onSubmit={handleTicketViewerLogin}>
              <div>
                <p className="eyebrow">Ticket Tracker</p>
                <h2>User login to check existing tickets</h2>
              </div>
              <div className="form-split">
                <label>
                  Name
                  <input value={loginForm.name} onChange={(e) => setLoginForm({ ...loginForm, name: e.target.value })} required />
                </label>
                <label>
                  Email
                  <input type="email" value={loginForm.email} onChange={(e) => setLoginForm({ ...loginForm, email: e.target.value })} required />
                </label>
              </div>
              <p className="helper-text">
                Sign in with the same email used while raising the ticket to view the latest status and admin updates.
              </p>
              {error ? <p className="error-banner">{error}</p> : null}
              <button className="primary-button" disabled={busy} type="submit">
                {busy ? 'Opening ticket tracker...' : 'Login And Check Ticket'}
              </button>
            </form>
          ) : (
            <form className="ticket-form auth-form" onSubmit={handleAdminLogin}>
              <div>
                <p className="eyebrow">Admin Access</p>
                <h2>Open the resolution console</h2>
              </div>
              <label>
                Admin name
                <input value={loginForm.name} onChange={(e) => setLoginForm({ ...loginForm, name: e.target.value })} required />
              </label>
              <label>
                Admin email
                <input type="email" value={loginForm.email} onChange={(e) => setLoginForm({ ...loginForm, email: e.target.value })} required />
              </label>
              <label>
                Department
                <select value={loginForm.department} onChange={(e) => setLoginForm({ ...loginForm, department: e.target.value })}>
                  <option value="IT Operations">IT Operations</option>
                  <option value="Service Desk">Service Desk</option>
                  <option value="Security Operations">Security Operations</option>
                </select>
              </label>
              {error ? <p className="error-banner">{error}</p> : null}
              <button className="primary-button" disabled={busy} type="submit">
                {busy ? 'Opening console...' : 'Login As Admin'}
              </button>
            </form>
          )}
        </section>
      </div>
    )
  }

  return (
    <div className="shell app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">
            {session.role === 'admin'
              ? 'Admin Resolution Console'
              : session.accessMode === 'ticket_viewer'
                ? 'User Ticket Tracker'
                : 'Employee Support Portal'}
          </p>
          <h1>IT Helpdesk Triage Agent</h1>
        </div>
        <div className="topbar-actions">
          <div className="identity-chip">
            <span>{session.name}</span>
            <small>{session.department}</small>
          </div>
          <button className="secondary-button" onClick={logout}>Log Out</button>
        </div>
      </header>

      {error ? <p className="error-banner">{error}</p> : null}
      {successMessage ? <p className="success-banner">{successMessage}</p> : null}

      {session.role === 'employee' && session.accessMode !== 'ticket_viewer' ? (
        <div className="layout employee-layout">
          <section className="panel form-panel">
            <p className="eyebrow">Create Ticket</p>
            <h2>Tell us what went wrong</h2>
            <form className="ticket-form" onSubmit={handleSubmitTicket}>
              <label>
                Ticket title
                <input value={ticketForm.title} onChange={(e) => setTicketForm({ ...ticketForm, title: e.target.value })} required />
              </label>
              <label>
                Description
                <textarea rows="8" value={ticketForm.description} onChange={(e) => setTicketForm({ ...ticketForm, description: e.target.value })} required />
              </label>
              <button className="primary-button" disabled={busy} type="submit">
                {busy ? 'Submitting...' : 'Submit Ticket'}
              </button>
            </form>
          </section>

          <section className="panel analysis-panel">
            <p className="eyebrow">AI Triage Result</p>
            <h2>What the agent did after submission</h2>
            {latestAnalysis ? (
              <div className="analysis-stack">
                <div className="stats-row three-up">
                  <MetricCard label="Severity" value={latestAnalysis.triage.severity} />
                  <MetricCard label="Route To" value={latestAnalysis.triage.assigned_team} />
                  <MetricCard label="Status" value={prettyStatus(latestAnalysis.status)} />
                </div>
                <div className="detail-block emphasis-block">
                  <strong>AI Summary</strong>
                  <p>{latestAnalysis.triage.summary}</p>
                </div>
                <div className="detail-grid single-mobile-grid">
                  <Detail title="Severity Classification" body={latestAnalysis.triage.severity_reason} />
                  <Detail title="Routing Decision" body={latestAnalysis.triage.routing_reason} />
                </div>
                <div className="detail-block response-block">
                  <strong>First-Person Reply Drafted For The Engineer</strong>
                  <p>{latestAnalysis.triage.first_response}</p>
                </div>
              </div>
            ) : (
              <EmptyState text="Submit a ticket and the AI agent will read it, classify severity, route it to the correct team, and draft the first engineer reply here." />
            )}
          </section>

          <section className="panel status-panel employee-status-panel">
            <div className="panel-header">
              <div>
                <p className="eyebrow">My Tickets</p>
                <h2>Status tracker</h2>
              </div>
              <button className="secondary-button" onClick={() => refreshData()}>Refresh</button>
            </div>
            <div className="stats-row three-up">
              <MetricCard label="Total" value={tickets.length} />
              <MetricCard label="Open" value={openCount} />
              <MetricCard label="Resolved" value={tickets.filter((ticket) => ticket.resolved).length} />
            </div>
            <div className="ticket-list">
              {tickets.length === 0 ? <EmptyState text="No tickets yet. Submit your first issue to start the workflow." /> : tickets.map((ticket) => (
                <article className="ticket-card" key={ticket.id}>
                  <div className="ticket-heading">
                    <div>
                      <h3>{ticket.title}</h3>
                      <p>{ticket.id}</p>
                    </div>
                    <span className={`badge badge-${ticket.status}`}>{prettyStatus(ticket.status)}</span>
                  </div>
                  <div className="ticket-meta">
                    <span className={`severity severity-${ticket.triage.severity.toLowerCase()}`}>{ticket.triage.severity}</span>
                    <span>{ticket.triage.assigned_team}</span>
                    <span>{ticket.resolved ? 'Resolved' : 'Not resolved'}</span>
                  </div>
                  <p>{ticket.triage.summary}</p>
                  <div className="detail-block">
                    <strong>Admin note</strong>
                    <p>{ticket.admin_note || 'No admin note yet.'}</p>
                  </div>
                </article>
              ))}
            </div>
          </section>
        </div>
      ) : session.role === 'employee' ? (
        <div className="layout ticket-view-layout">
          <section className="panel status-panel ticket-view-panel">
            <div className="panel-header">
              <div>
                <p className="eyebrow">My Tickets</p>
                <h2>Check your submitted tickets</h2>
              </div>
              <button className="secondary-button" onClick={() => refreshData()}>Refresh</button>
            </div>
            <div className="stats-row three-up">
              <MetricCard label="Total" value={tickets.length} />
              <MetricCard label="Open" value={openCount} />
              <MetricCard label="Resolved" value={tickets.filter((ticket) => ticket.resolved).length} />
            </div>
            <div className="ticket-list">
              {tickets.length === 0 ? <EmptyState text="No tickets found for this email yet." /> : tickets.map((ticket) => (
                <article className="ticket-card" key={ticket.id}>
                  <div className="ticket-heading">
                    <div>
                      <h3>{ticket.title}</h3>
                      <p>{ticket.id}</p>
                    </div>
                    <span className={`badge badge-${ticket.status}`}>{prettyStatus(ticket.status)}</span>
                  </div>
                  <div className="ticket-meta">
                    <span className={`severity severity-${ticket.triage.severity.toLowerCase()}`}>{ticket.triage.severity}</span>
                    <span>{ticket.triage.assigned_team}</span>
                    <span>{ticket.resolved ? 'Resolved' : 'Not resolved'}</span>
                  </div>
                  <p>{ticket.triage.summary}</p>
                  <div className="detail-grid single-mobile-grid">
                    <Detail title="Severity" body={ticket.triage.severity_reason} />
                    <Detail title="Routing" body={ticket.triage.routing_reason} />
                  </div>
                  <div className="detail-block">
                    <strong>Admin note</strong>
                    <p>{ticket.admin_note || 'No admin note yet.'}</p>
                  </div>
                </article>
              ))}
            </div>
          </section>
        </div>
      ) : (
        <div className="layout admin-layout">
          <section className="panel dashboard-panel">
            <div className="panel-header">
              <div>
                <p className="eyebrow">Overview</p>
                <h2>Resolution dashboard</h2>
              </div>
              <button className="secondary-button" onClick={() => refreshData()}>Refresh</button>
            </div>
            <div className="stats-row four-up">
              <MetricCard label="Total Tickets" value={dashboard?.total ?? 0} />
              <MetricCard label="Resolved" value={dashboard?.resolved ?? 0} />
              <MetricCard label="Unresolved" value={dashboard?.unresolved ?? 0} />
              <MetricCard label="Critical" value={dashboard?.by_severity?.Critical ?? 0} />
            </div>
          </section>

          <section className="panel tickets-panel">
            <p className="eyebrow">Admin Queue</p>
            <h2>Analyzed tickets awaiting action</h2>
            <div className="ticket-list">
              {adminVisibleTickets.length === 0 ? <EmptyState text="No active tickets in the admin queue." /> : adminVisibleTickets.map((ticket) => {
                const draft = adminDrafts[ticket.id] || { admin_note: ticket.admin_note }
                return (
                  <article className="ticket-card admin-card" key={ticket.id}>
                    <div className="ticket-heading">
                      <div>
                        <h3>{ticket.title}</h3>
                        <p>{ticket.requester_name} · {ticket.requester_email}</p>
                      </div>
                      <div className="heading-side">
                        <span className={`severity severity-${ticket.triage.severity.toLowerCase()}`}>{ticket.triage.severity}</span>
                        <span className={`badge badge-${ticket.status}`}>{prettyStatus(ticket.status)}</span>
                      </div>
                    </div>
                    <div className="ticket-meta">
                      <span>{ticket.department}</span>
                      <span>{ticket.triage.assigned_team}</span>
                      <span>{ticket.reviewed_by_admin ? `Reviewed by ${ticket.admin_name}` : 'Awaiting admin review'}</span>
                    </div>
                    <div className="detail-grid">
                      <Detail title="Issue description" body={ticket.description} />
                      <Detail title="AI summary" body={ticket.triage.summary} />
                      <Detail title="Severity reason" body={ticket.triage.severity_reason} />
                      <Detail title="Routing reason" body={ticket.triage.routing_reason} />
                      <Detail title="Suggested first response" body={ticket.triage.first_response} />
                    </div>
                    <div className="actions-grid admin-actions-grid">
                      <div className="admin-button-row full-width">
                        <button className="action-button resolve-button" disabled={busy} onClick={() => handleAdminUpdate(ticket.id, 'resolved')}>
                          Resolve Ticket
                        </button>
                        <button className="action-button progress-button" disabled={busy} onClick={() => handleAdminUpdate(ticket.id, 'in_progress')}>
                          Mark In Progress
                        </button>
                        <button className="action-button reach-button" disabled={busy} onClick={() => handleAdminUpdate(ticket.id, 'could_not_reach')}>
                          Could Not Reach
                        </button>
                      </div>
                      <label className="full-width">
                        Admin note
                        <textarea rows="3" value={draft.admin_note} onChange={(e) => setAdminDrafts({ ...adminDrafts, [ticket.id]: { ...draft, admin_note: e.target.value } })} placeholder="Add what you did or why the status changed" />
                      </label>
                    </div>
                  </article>
                )
              })}
            </div>
          </section>
        </div>
      )}
    </div>
  )
}

function buildTicketStatusMessage(ticket) {
  return `Ticket ${ticket.id} was submitted successfully. Current status: ${prettyStatus(ticket.status)}. Assigned team: ${ticket.triage.assigned_team}. Severity: ${ticket.triage.severity}.`
}

function prettyStatus(status) {
  return status.replaceAll('_', ' ').replace(/\b\w/g, (match) => match.toUpperCase())
}

function prettyTicketOwner(requesterName, requesterEmail) {
  return `${requesterName} - ${requesterEmail}`
}

function MetricCard({ label, value }) {
  return (
    <div className="metric-card">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  )
}

function Detail({ title, body }) {
  return (
    <div className="detail-block">
      <strong>{title}</strong>
      <p>{body}</p>
    </div>
  )
}

function EmptyState({ text }) {
  return <div className="empty-state">{text}</div>
}
