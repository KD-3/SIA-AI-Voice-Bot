import React, { useState } from 'react';
import { Bot, Phone, Building2, MapPin, Briefcase, Activity, CheckCircle2, AlertCircle, Loader2, Sparkles, Users } from 'lucide-react';
import './index.css';

// Multiple dummy leads for completeness
const LEADS_DATABASE = [
  {
    id: 1,
    name: "Kaustubh Dixit",
    title: "Co-founder - SIA",
    company: "SIA Intelligence",
    phone: "+919919837374",
    turnover: "1 Crore",
    location: "Bangalore, India",
    status: "Warm Lead",
    initials: "KD"
  },
  {
    id: 2,
    name: "Ramesh Kumar",
    title: "Proprietor",
    company: "Kumar Electronics & Co.",
    phone: "+919876543210",
    turnover: "45 Lakhs",
    location: "Mumbai, India",
    status: "Cold Outreach",
    initials: "RK"
  },
  {
    id: 3,
    name: "Priya Sharma",
    title: "Retail Director",
    company: "Sharma Supermarts Pvt Ltd",
    phone: "+919876543211",
    turnover: "5 Crores",
    location: "Delhi, India",
    status: "Follow-up",
    initials: "PS"
  }
];

function App() {
  const [activeLeadId, setActiveLeadId] = useState(1);
  const [isCalling, setIsCalling] = useState(false);
  const [status, setStatus] = useState(null);

  const activeLead = LEADS_DATABASE.find(l => l.id === activeLeadId);

  const handleCall = async () => {
    setIsCalling(true);
    setStatus(null);

    try {
      const response = await fetch('http://localhost:8000/api/calls/outbound', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone_number: activeLead.phone })
      });
      
      const data = await response.json();
      
      if (data.success) {
        setStatus('success');
        setTimeout(() => setStatus(null), 8000);
      } else {
        setStatus('error');
      }
    } catch (err) {
      console.error(err);
      setStatus('error');
    } finally {
      setIsCalling(false);
    }
  };

  return (
    <div className="dashboard">
      
      {/* Sidebar Layout */}
      <div className="sidebar">
        <div className="logo-container">
          {/* Paytm Official Logo SVG via Wikimedia */}
          <img src="https://upload.wikimedia.org/wikipedia/commons/2/24/Paytm_Logo_%28standalone%29.svg" alt="Paytm" />
          <div className="system-title">Merchant Intelligence CRM</div>
        </div>

        <div className="leads-list">
          {LEADS_DATABASE.map(lead => (
            <div 
              key={lead.id} 
              className={`lead-nav-item ${activeLeadId === lead.id ? 'active' : ''}`}
              onClick={() => { setActiveLeadId(lead.id); setStatus(null); }}
            >
              <div className="lead-nav-avatar">{lead.initials}</div>
              <div className="lead-nav-info">
                <div className="lead-nav-name">{lead.name}</div>
                <div className="lead-nav-company">{lead.company}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Main Content Layout */}
      <div className="main-content">
        <div className="header-actions">
          <div>
            <h1 style={{fontSize: "1.5rem", color: "var(--primary-dark)", fontWeight: "700", marginBottom: "0.25rem"}}>
              Lead 360 Analytics
            </h1>
            <p style={{color: "var(--text-muted)", fontSize: "0.9rem"}}>
              Manage active merchant pipelines and dispatch AI sales agents instantly.
            </p>
          </div>
          <span className="badge">
            <Activity size={14} /> System Online
          </span>
        </div>

        <div className="crm-grid">
          
          {/* Left Column - Active Lead Profile */}
          <div className="card">
            <div className="card-title">
              <Users size={18} /> Profile Overview
            </div>
            
            <div className="lead-header">
              <div className="lead-avatar">{activeLead.initials}</div>
              <div>
                <div className="lead-name">{activeLead.name}</div>
                <div className="lead-title">{activeLead.title}</div>
              </div>
            </div>

            <div className="info-grid">
              <div className="info-item">
                <span className="info-label">Direct Contact</span>
                <span className="info-value"><Phone size={16} color="var(--primary)" /> {activeLead.phone}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Annual Turnover</span>
                <span className="info-value"><Building2 size={16} color="var(--primary)" /> {activeLead.turnover}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Geographic Base</span>
                <span className="info-value"><MapPin size={16} color="var(--primary)" /> {activeLead.location}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Pipeline Status</span>
                <span className="info-value" style={{color: "var(--success)"}}>
                  <CheckCircle2 size={16} /> {activeLead.status}
                </span>
              </div>
            </div>
          </div>

          {/* Right Column - Action Panel */}
          <div className="card action-card">
            <div className="bot-avatar">
              <div className={`pulse ${isCalling ? 'active' : ''}`}></div>
              <Bot size={36} />
            </div>
            
            <div className="bot-title">Sia Voice Agent</div>
            <div className="bot-desc">Dispatch automated merchant setup pitch to {activeLead.name.split(' ')[0]}.</div>

            <button 
              className="primary-btn" 
              onClick={handleCall}
              disabled={isCalling}
            >
              {isCalling ? (
                <><Loader2 className="animate-spin" size={18} /> Bridging Call...</>
              ) : (
                <><Phone size={18} /> Dispatch AI Pitch</>
              )}
            </button>

            {status === 'success' && (
              <div className="status-badge success">
                <CheckCircle2 size={16} /> Contact sequence dispatched!
              </div>
            )}

            {status === 'error' && (
              <div className="status-badge error">
                <AlertCircle size={16} /> Agent bridge failed.
              </div>
            )}
          </div>

        </div>
      </div>
    </div>
  );
}

export default App;
