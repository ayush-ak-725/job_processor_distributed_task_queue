import React, { useState, useEffect, useCallback } from 'react'
import './index.css'

// Use environment variables or defaults
const API_URL = import.meta.env.VITE_API_URL 
  ? `${import.meta.env.VITE_API_URL}/api/v1` 
  : '/api/v1'
const WS_URL = import.meta.env.VITE_WS_URL 
  ? import.meta.env.VITE_WS_URL.replace('http', 'ws') 
  : (window.location.protocol === 'https:' ? 'wss://' : 'ws://') + window.location.host + '/ws'

function App() {
  const [jobs, setJobs] = useState([])
  const [metrics, setMetrics] = useState({
    total_jobs: 0,
    pending_jobs: 0,
    running_jobs: 0,
    completed_jobs: 0,
    failed_jobs: 0,
    dlq_jobs: 0,
  })
  const [activeTab, setActiveTab] = useState('all')
  const [wsConnected, setWsConnected] = useState(false)
  const [apiKey, setApiKey] = useState(localStorage.getItem('apiKey') || '')
  const [submitPayload, setSubmitPayload] = useState('{"task": "example", "data": {}}')
  const [submitIdempotencyKey, setSubmitIdempotencyKey] = useState('')
  const [submitMaxRetries, setSubmitMaxRetries] = useState(3)
  const [submitError, setSubmitError] = useState('')
  const [submitSuccess, setSubmitSuccess] = useState('')
  const [loading, setLoading] = useState(false)

  // WebSocket connection
  useEffect(() => {
    if (!apiKey) return

    const ws = new WebSocket(WS_URL)
    
    ws.onopen = () => {
      setWsConnected(true)
      console.log('WebSocket connected')
    }
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      console.log('WebSocket message:', data)
      // Refresh jobs and metrics on events
      fetchJobs()
      fetchMetrics()
    }
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
      setWsConnected(false)
    }
    
    ws.onclose = () => {
      setWsConnected(false)
      console.log('WebSocket disconnected')
      // Reconnect after 3 seconds
      setTimeout(() => {
        if (apiKey) {
          // Reconnect logic handled by useEffect
        }
      }, 3000)
    }
    
    return () => {
      ws.close()
    }
  }, [apiKey])

  const fetchJobs = useCallback(async () => {
    if (!apiKey) return
    
    try {
      const response = await fetch(`${API_URL}/jobs`, {
        headers: {
          'Authorization': `Bearer ${apiKey}`,
        },
      })
      
      if (response.ok) {
        const data = await response.json()
        setJobs(data.jobs || [])
      }
    } catch (error) {
      console.error('Error fetching jobs:', error)
    }
  }, [apiKey])

  const fetchMetrics = useCallback(async () => {
    if (!apiKey) return
    
    try {
      const response = await fetch(`${API_URL}/jobs/metrics/summary`, {
        headers: {
          'Authorization': `Bearer ${apiKey}`,
        },
      })
      
      if (response.ok) {
        const data = await response.json()
        setMetrics(data)
      }
    } catch (error) {
      console.error('Error fetching metrics:', error)
    }
  }, [apiKey])

  useEffect(() => {
    if (apiKey) {
      fetchJobs()
      fetchMetrics()
      const interval = setInterval(() => {
        fetchJobs()
        fetchMetrics()
      }, 5000) // Poll every 5 seconds as fallback
      return () => clearInterval(interval)
    }
  }, [apiKey, fetchJobs, fetchMetrics])

  const handleSubmitJob = async (e) => {
    e.preventDefault()
    setSubmitError('')
    setSubmitSuccess('')
    setLoading(true)
    
    try {
      let payload
      try {
        payload = JSON.parse(submitPayload)
      } catch (e) {
        setSubmitError('Invalid JSON payload')
        setLoading(false)
        return
      }
      
      const requestBody = {
        payload,
        max_retries: submitMaxRetries,
      }
      
      if (submitIdempotencyKey) {
        requestBody.idempotency_key = submitIdempotencyKey
      }
      
      const response = await fetch(`${API_URL}/jobs`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${apiKey}`,
        },
        body: JSON.stringify(requestBody),
      })
      
      const data = await response.json()
      
      if (response.ok) {
        setSubmitSuccess(`Job submitted successfully! Job ID: ${data.id}`)
        setSubmitPayload('{"task": "example", "data": {}}')
        setSubmitIdempotencyKey('')
        fetchJobs()
        fetchMetrics()
      } else {
        setSubmitError(data.detail || 'Failed to submit job')
      }
    } catch (error) {
      setSubmitError(`Error: ${error.message}`)
    } finally {
      setLoading(false)
    }
  }

  const filteredJobs = jobs.filter(job => {
    if (activeTab === 'all') return true
    return job.status === activeTab
  })

  const getStatusCount = (status) => {
    if (status === 'all') return jobs.length
    return jobs.filter(j => j.status === status).length
  }

  return (
    <div className="container">
      <div className="header">
        <h1>📋 Job Processor Dashboard</h1>
        <p>
          <span className={`connection-status ${wsConnected ? 'connected' : 'disconnected'}`}></span>
          {wsConnected ? 'Connected (Live Updates)' : 'Disconnected (Polling)'}
        </p>
      </div>

      <div className="submit-form">
        <h2>Submit New Job</h2>
        <div className="form-group">
          <label>API Key</label>
          <input
            type="password"
            value={apiKey}
            onChange={(e) => {
              const key = e.target.value
              setApiKey(key)
              localStorage.setItem('apiKey', key)
            }}
            placeholder="Enter your API key"
          />
        </div>
        <form onSubmit={handleSubmitJob}>
          <div className="form-group">
            <label>Job Payload (JSON)</label>
            <textarea
              value={submitPayload}
              onChange={(e) => setSubmitPayload(e.target.value)}
              placeholder='{"task": "process_data", "data": {...}}'
            />
          </div>
          <div className="form-group">
            <label>Idempotency Key (Optional)</label>
            <input
              type="text"
              value={submitIdempotencyKey}
              onChange={(e) => setSubmitIdempotencyKey(e.target.value)}
              placeholder="unique-key-123"
            />
          </div>
          <div className="form-group">
            <label>Max Retries</label>
            <input
              type="number"
              value={submitMaxRetries}
              onChange={(e) => setSubmitMaxRetries(parseInt(e.target.value))}
              min="0"
              max="10"
            />
          </div>
          {submitError && <div className="error">{submitError}</div>}
          {submitSuccess && <div className="success">{submitSuccess}</div>}
          <button type="submit" className="btn" disabled={!apiKey || loading}>
            {loading ? 'Submitting...' : 'Submit Job'}
          </button>
        </form>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <h3>Total Jobs</h3>
          <div className="value">{metrics.total_jobs}</div>
        </div>
        <div className="stat-card pending">
          <h3>Pending</h3>
          <div className="value">{metrics.pending_jobs}</div>
        </div>
        <div className="stat-card running">
          <h3>Running</h3>
          <div className="value">{metrics.running_jobs}</div>
        </div>
        <div className="stat-card completed">
          <h3>Completed</h3>
          <div className="value">{metrics.completed_jobs}</div>
        </div>
        <div className="stat-card failed">
          <h3>Failed</h3>
          <div className="value">{metrics.failed_jobs}</div>
        </div>
        <div className="stat-card dlq">
          <h3>DLQ</h3>
          <div className="value">{metrics.dlq_jobs}</div>
        </div>
      </div>

      <div className="tabs">
        <button
          className={`tab ${activeTab === 'all' ? 'active' : ''}`}
          onClick={() => setActiveTab('all')}
        >
          All ({getStatusCount('all')})
        </button>
        <button
          className={`tab ${activeTab === 'pending' ? 'active' : ''}`}
          onClick={() => setActiveTab('pending')}
        >
          Pending ({getStatusCount('pending')})
        </button>
        <button
          className={`tab ${activeTab === 'running' ? 'active' : ''}`}
          onClick={() => setActiveTab('running')}
        >
          Running ({getStatusCount('running')})
        </button>
        <button
          className={`tab ${activeTab === 'completed' ? 'active' : ''}`}
          onClick={() => setActiveTab('completed')}
        >
          Completed ({getStatusCount('completed')})
        </button>
        <button
          className={`tab ${activeTab === 'failed' ? 'active' : ''}`}
          onClick={() => setActiveTab('failed')}
        >
          Failed ({getStatusCount('failed')})
        </button>
        <button
          className={`tab ${activeTab === 'dlq' ? 'active' : ''}`}
          onClick={() => setActiveTab('dlq')}
        >
          DLQ ({getStatusCount('dlq')})
        </button>
      </div>

      <div className="job-list">
        {loading && <div className="loading">Loading...</div>}
        {!loading && filteredJobs.length === 0 && (
          <div className="empty">No jobs found</div>
        )}
        {!loading && filteredJobs.map((job) => (
          <div key={job.id} className="job-item">
            <div className="job-header">
              <div>
                <div className="job-id">ID: {job.id}</div>
                <div className="job-meta">
                  <span>Tenant: {job.tenant_id}</span>
                  <span>Trace: {job.trace_id}</span>
                  {job.idempotency_key && (
                    <span>Idempotency: {job.idempotency_key}</span>
                  )}
                </div>
              </div>
              <span className={`job-status ${job.status}`}>{job.status}</span>
            </div>
            <div className="job-meta">
              <span>Retries: {job.retry_count}/{job.max_retries}</span>
              <span>Created: {new Date(job.created_at).toLocaleString()}</span>
              {job.started_at && (
                <span>Started: {new Date(job.started_at).toLocaleString()}</span>
              )}
              {job.completed_at && (
                <span>Completed: {new Date(job.completed_at).toLocaleString()}</span>
              )}
            </div>
            {job.error_message && (
              <div className="error" style={{ marginTop: '10px' }}>
                Error: {job.error_message}
              </div>
            )}
            <div className="job-payload">
              {JSON.stringify(job.payload, null, 2)}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default App

