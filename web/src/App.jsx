import React, { useState, useEffect, useRef } from 'react';
import {
  Bot, Phone, Building2, MapPin, CheckCircle2,
  AlertCircle, Loader2, Activity, Users,
  Sparkles, Clock, Star, Zap, MessageSquare
} from 'lucide-react';
import './index.css';

const API = 'http://localhost:8000';

const LEADS = [
  {
    id: 1, name: "Kaustubh Dixit", title: "Co-founder - SIA",
    company: "SIA Intelligence", phone: "+919919837374",
    turnover: "₹1 Crore", location: "Bangalore, India",
    status: "Warm Lead", initials: "KD"
  },
  {
    id: 2, name: "Ramesh Kumar", title: "Proprietor",
    company: "Kumar Electronics & Co.", phone: "+919876543210",
    turnover: "₹45 Lakhs", location: "Mumbai, India",
    status: "Cold Outreach", initials: "RK"
  },
  {
    id: 3, name: "Priya Sharma", title: "Retail Director",
    company: "Sharma Supermarts Pvt Ltd", phone: "+919876543211",
    turnover: "₹5 Crores", location: "Delhi, India",
    status: "Follow-up", initials: "PS"
  }
];

function StarRating({ value }) {
  return (
    <div className="rating-stars">
      {[1, 2, 3, 4, 5].map(n => (
        <span key={n} className="star">{n <= value ? '★' : '☆'}</span>
      ))}
    </div>
  );
}

function PostCallPanel({ data }) {
  const mins = Math.floor(data.duration_seconds / 60);
  const secs = data.duration_seconds % 60;

  return (
    <div className="post-call-panel">
      <div className="post-call-header">
        <h2><CheckCircle2 size={18} /> Call Completed — Post-Call Analysis</h2>
        <div className="meta-row">
          <span className="meta-badge">
            <Clock size={12} style={{ marginRight: 4 }} />
            {mins}m {secs}s
          </span>
          <span className="meta-badge">Session: {data.session_id?.slice(-8)}</span>
        </div>
      </div>

      <div className="panel-body">
        {/* Transcript Column */}
        <div className="transcript-col">
          <div className="col-heading"><MessageSquare size={13} style={{ display: 'inline', marginRight: 4 }} />Full Transcript</div>
          <div className="transcript-scroll">
            {data.transcript.map((t, i) => (
              <div key={i} className="turn">
                <span className={`turn-role ${t.role === 'user' ? 'user' : 'ai'}`}>
                  {t.role === 'user' ? 'YOU' : 'SIA'}
                </span>
                <span className="turn-text">{t.text}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Insights Column */}
        <div className="insights-col">
          <div className="col-heading"><Zap size={13} style={{ display: 'inline', marginRight: 4 }} />AI Insights</div>

          {/* Sentiment */}
          <div className={`sentiment-chip ${data.sentiment}`}>
            {data.sentiment === 'Positive' ? '😊' : data.sentiment === 'Neutral' ? '😐' : '😟'}
            {data.sentiment}
          </div>

          {/* Lead Rating */}
          <div className="col-heading">Lead Rating</div>
          <div className="rating-row" style={{ marginBottom: '1.25rem' }}>
            <StarRating value={data.lead_rating} />
            <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginLeft: '0.5rem' }}>
              {data.lead_rating}/5
            </span>
          </div>

          {/* Summary */}
          <div className="col-heading">Summary</div>
          <div className="summary-text">{data.summary}</div>

          {/* Key Highlights */}
          <div className="col-heading">Key Highlights</div>
          <ul className="highlights-list">
            {data.key_highlights?.map((h, i) => (
              <li key={i} className="highlight-item">
                <span className="highlight-icon"><CheckCircle2 size={14} /></span> {h}
              </li>
            ))}
          </ul>

          {/* Next Actions */}
          <div className="col-heading">Recommended Next Actions</div>
          <ul className="actions-list">
            {data.next_actions?.map((a, i) => (
              <li key={i} className="action-item">
                <span className="action-icon"><Zap size={14} /></span> {a}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}

export default function App() {
  const [activeId, setActiveId] = useState(1);
  const [isCalling, setIsCalling] = useState(false);
  const [callStatus, setCallStatus] = useState(null); // null | 'dispatched' | 'polling' | 'ready' | 'error'
  const [summary, setSummary] = useState(null);
  const pollRef = useRef(null);

  const lead = LEADS.find(l => l.id === activeId);

  // Stop polling when unmounted or lead changes
  useEffect(() => {
    return () => clearInterval(pollRef.current);
  }, []);

  const startPolling = () => {
    setCallStatus('polling');
    pollRef.current = setInterval(async () => {
      try {
        const res = await fetch(`${API}/api/calls/latest/summary`);
        const data = await res.json();
        if (data.ready) {
          clearInterval(pollRef.current);
          setSummary(data.data);
          setCallStatus('ready');
        }
      } catch { /* server might restart, keep polling */ }
    }, 5000);
  };

  const handleCall = async () => {
    setIsCalling(true);
    setCallStatus(null);
    setSummary(null);

    try {
      const res = await fetch(`${API}/api/calls/outbound`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone_number: lead.phone })
      });
      const data = await res.json();
      if (data.success) {
        setCallStatus('dispatched');
        // Start polling for summary after a brief delay (call needs time)
        setTimeout(startPolling, 5000);
      } else {
        setCallStatus('error');
      }
    } catch {
      setCallStatus('error');
    } finally {
      setIsCalling(false);
    }
  };

  const handleLeadChange = (id) => {
    clearInterval(pollRef.current);
    setActiveId(id);
    setCallStatus(null);
    setSummary(null);
  };

  return (
    <div className="dashboard">
      {/* Sidebar */}
      <div className="sidebar">
        <div className="logo-container">
          <img src="https://upload.wikimedia.org/wikipedia/commons/2/24/Paytm_Logo_%28standalone%29.svg" alt="Paytm" />
          <div className="system-title">Merchant Intelligence CRM</div>
        </div>
        <div className="leads-list">
          {LEADS.map(l => (
            <div key={l.id} className={`lead-nav-item ${activeId === l.id ? 'active' : ''}`} onClick={() => handleLeadChange(l.id)}>
              <div className="lead-nav-avatar">{l.initials}</div>
              <div>
                <div className="lead-nav-name">{l.name}</div>
                <div className="lead-nav-company">{l.company}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Main */}
      <div className="main-content">
        <div className="page-header">
          <div>
            <h1 style={{ fontSize: '1.4rem', color: 'var(--primary-dark)', fontWeight: 700, marginBottom: '0.2rem' }}>Lead 360 Analytics</h1>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.88rem' }}>Dispatch AI agent and review post-call intelligence instantly.</p>
          </div>
          <span className="system-badge"><Activity size={13} /> System Online</span>
        </div>

        {/* Top Grid: Lead Profile + Action */}
        <div className="crm-top">
          <div className="card">
            <div className="card-title"><Users size={16} /> Profile Overview</div>
            <div className="lead-header">
              <div className="lead-avatar">{lead.initials}</div>
              <div>
                <div className="lead-name">{lead.name}</div>
                <div className="lead-title">{lead.title}</div>
              </div>
            </div>
            <div className="info-grid">
              <div>
                <div className="info-label">Direct Contact</div>
                <div className="info-value"><Phone size={14} color="var(--primary)" /> {lead.phone}</div>
              </div>
              <div>
                <div className="info-label">Annual Turnover</div>
                <div className="info-value"><Building2 size={14} color="var(--primary)" /> {lead.turnover}</div>
              </div>
              <div>
                <div className="info-label">Location</div>
                <div className="info-value"><MapPin size={14} color="var(--primary)" /> {lead.location}</div>
              </div>
              <div>
                <div className="info-label">Pipeline Status</div>
                <div className="info-value" style={{ color: 'var(--success)' }}><CheckCircle2 size={14} /> {lead.status}</div>
              </div>
            </div>
          </div>

          <div className="card action-card">
            <div className="bot-avatar">
              <div className={`pulse ${isCalling ? 'active' : ''}`}></div>
              <Bot size={32} />
            </div>
            <div className="bot-title">Sia Voice Agent</div>
            <div className="bot-desc">Dispatch a personalized Paytm pitch to {lead.name.split(' ')[0]}.</div>

            <button className="primary-btn" onClick={handleCall} disabled={isCalling || callStatus === 'polling'}>
              {isCalling ? <><Loader2 className="animate-spin" size={16} /> Bridging...</>
                : callStatus === 'polling' ? <><Loader2 className="animate-spin" size={16} /> Awaiting Summary...</>
                : <><Phone size={16} /> Dispatch AI Pitch</>}
            </button>

            {callStatus === 'dispatched' && (
              <div className="status-mini polling">
                <Sparkles size={14} /> Call dispatched! Analyzing after call ends...
              </div>
            )}
            {callStatus === 'polling' && (
              <div className="status-mini polling">
                <Loader2 size={14} /> Polling for post-call intelligence...
              </div>
            )}
            {callStatus === 'ready' && (
              <div className="status-mini success">
                <CheckCircle2 size={14} /> Analysis ready — see below!
              </div>
            )}
            {callStatus === 'error' && (
              <div className="status-mini error">
                <AlertCircle size={14} /> Bridge failed. Check server.
              </div>
            )}
          </div>
        </div>

        {/* Post-Call Panel */}
        {summary && <PostCallPanel data={summary} />}
      </div>
    </div>
  );
}
