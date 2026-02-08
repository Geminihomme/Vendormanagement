/**
 * RISK DASHBOARD PAGE (The Vendor "Credit Report" Center)
 * =========================================================
 * This is where managers see the risk profile of all vendors at a glance.
 *
 * LAYOUT:
 * 1. Summary stat cards (Low | Medium | High | Critical | Average)
 * 2. Tab bar (All Vendors | Alerts | Vendor Detail)
 * 3. Table of vendors sorted by risk score (highest first)
 * 4. Alerts view showing vendors above the threshold
 * 5. "Recalculate All" button to refresh scores
 *
 * HOW TO READ THE DASHBOARD:
 * - Green rows (0-25): These vendors are solid. Low maintenance.
 * - Yellow rows (26-50): Keep an eye on these. Review at next check-in.
 * - Orange rows (51-75): Action needed. Check contracts, payments, docs.
 * - Red rows (76-100): Urgent. Something is seriously wrong. Fix immediately.
 *
 * Think of it like a car dashboard — green lights mean everything is fine,
 * yellow means "check engine soon," red means "pull over NOW."
 */

import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { RiskDashboardItem, RiskSummary, RiskAlert, RiskScoreResponse } from '../types/risk';
import {
  getRiskSummary,
  getRiskDashboard,
  getRiskAlerts,
  getVendorRisk,
  recalculateAllRisks,
} from '../services/api';

function RiskDashboard() {
  const [summary, setSummary] = useState<RiskSummary>({
    low: 0, medium: 0, high: 0, critical: 0, total: 0, average_score: 0,
  });
  const [vendors, setVendors] = useState<RiskDashboardItem[]>([]);
  const [alerts, setAlerts] = useState<RiskAlert[]>([]);
  const [activeTab, setActiveTab] = useState<'vendors' | 'alerts' | 'detail'>('vendors');
  const [selectedVendor, setSelectedVendor] = useState<RiskScoreResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [recalculating, setRecalculating] = useState(false);
  const [error, setError] = useState('');

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const [summaryData, vendorData, alertData] = await Promise.all([
        getRiskSummary(),
        getRiskDashboard(),
        getRiskAlerts(),
      ]);
      setSummary(summaryData);
      setVendors(vendorData);
      setAlerts(alertData);
    } catch {
      setError('Failed to load risk data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleRecalculateAll = async () => {
    setRecalculating(true);
    setError('');
    try {
      await recalculateAllRisks();
      await loadData();
    } catch {
      setError('Failed to recalculate risk scores');
    } finally {
      setRecalculating(false);
    }
  };

  const handleViewDetail = async (vendorId: number) => {
    try {
      const detail = await getVendorRisk(vendorId);
      setSelectedVendor(detail);
      setActiveTab('detail');
    } catch {
      setError('Failed to load vendor risk detail');
    }
  };

  const riskLevelColor = (level: string) => {
    switch (level) {
      case 'critical': return '#dc3545';
      case 'high': return '#fd7e14';
      case 'medium': return '#ffc107';
      case 'low': return '#28a745';
      default: return '#888';
    }
  };

  const riskLevelClass = (level: string) => `risk-${level}`;

  if (loading) return <div className="loading">Loading risk assessments...</div>;

  return (
    <div>
      <div className="page-header">
        <h1>Risk Dashboard</h1>
        <button
          className="btn btn-primary"
          onClick={handleRecalculateAll}
          disabled={recalculating}
        >
          {recalculating ? 'Recalculating...' : 'Recalculate All'}
        </button>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {/* Summary stat cards */}
      <div className="stats-row" style={{ gridTemplateColumns: 'repeat(5, 1fr)' }}>
        <div className="stat-card stat-total">
          <div className="stat-number">{summary.low}</div>
          <div className="stat-label">Low Risk</div>
        </div>
        <div className="stat-card stat-attention">
          <div className="stat-number">{summary.medium}</div>
          <div className="stat-label">Medium</div>
        </div>
        <div className="stat-card stat-warning">
          <div className="stat-number">{summary.high}</div>
          <div className="stat-label">High Risk</div>
        </div>
        <div className="stat-card stat-expired">
          <div className="stat-number">{summary.critical}</div>
          <div className="stat-label">Critical</div>
        </div>
        <div className="stat-card">
          <div className="stat-number">{summary.average_score}</div>
          <div className="stat-label">Avg Score</div>
        </div>
      </div>

      {/* Tab bar */}
      <div className="tab-bar">
        <button
          className={`tab-btn ${activeTab === 'vendors' ? 'tab-active' : ''}`}
          onClick={() => setActiveTab('vendors')}
        >
          All Vendors ({summary.total})
        </button>
        <button
          className={`tab-btn ${activeTab === 'alerts' ? 'tab-active' : ''}`}
          onClick={() => setActiveTab('alerts')}
        >
          Alerts
          {alerts.length > 0 && (
            <span className="notification-badge">{alerts.length}</span>
          )}
        </button>
        {selectedVendor && (
          <button
            className={`tab-btn ${activeTab === 'detail' ? 'tab-active' : ''}`}
            onClick={() => setActiveTab('detail')}
          >
            Detail: {selectedVendor.vendor_name}
          </button>
        )}
      </div>

      {/* Tab content */}
      {activeTab === 'vendors' && (
        <div>
          {vendors.length === 0 ? (
            <div className="empty-state">
              <p>No vendors to assess. Add vendors first, then recalculate.</p>
            </div>
          ) : (
            <table className="data-table">
              <thead>
                <tr>
                  <th>Vendor</th>
                  <th>Category</th>
                  <th>Risk Score</th>
                  <th>Level</th>
                  <th>Contracts</th>
                  <th>Value</th>
                  <th>Overdue</th>
                  <th>Expiring</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {vendors.map((v) => (
                  <tr key={v.vendor_id} className={riskLevelClass(v.risk_level)}>
                    <td>
                      <Link to={`/vendors/${v.vendor_id}`}>{v.vendor_name}</Link>
                    </td>
                    <td>{v.category || '—'}</td>
                    <td>
                      <div className="risk-score-bar">
                        <div
                          className="risk-score-fill"
                          style={{
                            width: `${v.overall_score}%`,
                            backgroundColor: riskLevelColor(v.risk_level),
                          }}
                        />
                        <span className="risk-score-label">{v.overall_score}</span>
                      </div>
                    </td>
                    <td>
                      <span className={`risk-badge risk-badge-${v.risk_level}`}>
                        {v.risk_level}
                      </span>
                    </td>
                    <td>{v.contract_count}</td>
                    <td>${v.total_contract_value.toLocaleString()}</td>
                    <td>
                      {v.overdue_payments > 0 ? (
                        <span style={{ color: '#dc3545', fontWeight: 600 }}>{v.overdue_payments}</span>
                      ) : '0'}
                    </td>
                    <td>
                      {v.expiring_soon > 0 ? (
                        <span style={{ color: '#fd7e14', fontWeight: 600 }}>{v.expiring_soon}</span>
                      ) : '0'}
                    </td>
                    <td>
                      <button
                        className="btn btn-sm btn-secondary"
                        onClick={() => handleViewDetail(v.vendor_id)}
                      >
                        Details
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {activeTab === 'alerts' && (
        <div>
          {alerts.length === 0 ? (
            <div className="empty-state">
              <p>No risk alerts. All vendors are within acceptable thresholds.</p>
            </div>
          ) : (
            <div className="approval-list">
              {alerts.map((alert) => (
                <div
                  key={alert.vendor_id}
                  className={`approval-card approval-${alert.risk_level === 'critical' ? 'rejected' : 'pending'}`}
                >
                  <div className="approval-card-header">
                    <div>
                      <span className={`risk-badge risk-badge-${alert.risk_level}`}>
                        {alert.risk_level}
                      </span>
                      <strong style={{ fontSize: '20px', marginLeft: '8px' }}>
                        {alert.overall_score}/100
                      </strong>
                    </div>
                  </div>
                  <h3 className="approval-title">
                    <Link to={`/vendors/${alert.vendor_id}`}>{alert.vendor_name}</Link>
                  </h3>
                  <p className="approval-comment" style={{ margin: '8px 0' }}>
                    {alert.alert_reason}
                  </p>
                  <button
                    className="btn btn-sm btn-primary"
                    onClick={() => handleViewDetail(alert.vendor_id)}
                  >
                    View Full Report
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {activeTab === 'detail' && selectedVendor && (
        <div className="risk-detail">
          <div className="risk-detail-header">
            <h2>
              <Link to={`/vendors/${selectedVendor.vendor_id}`}>
                {selectedVendor.vendor_name}
              </Link>
            </h2>
            <div className="risk-detail-overall">
              <span
                className="risk-detail-score"
                style={{ color: riskLevelColor(selectedVendor.risk_level) }}
              >
                {selectedVendor.overall_score}
              </span>
              <span className="risk-detail-max">/100</span>
              <span className={`risk-badge risk-badge-${selectedVendor.risk_level}`} style={{ marginLeft: '12px' }}>
                {selectedVendor.risk_level} risk
              </span>
            </div>
          </div>

          <div className="risk-factors">
            {selectedVendor.factors.map((factor) => (
              <div key={factor.name} className="risk-factor-card">
                <div className="risk-factor-header">
                  <strong>{factor.name}</strong>
                  <span>
                    {factor.score}/{factor.max_score}
                  </span>
                </div>
                <div className="risk-score-bar" style={{ height: '10px' }}>
                  <div
                    className="risk-score-fill"
                    style={{
                      width: `${(factor.score / factor.max_score) * 100}%`,
                      backgroundColor: factor.score >= 16 ? '#dc3545' : factor.score >= 8 ? '#fd7e14' : '#28a745',
                    }}
                  />
                </div>
                <p className="risk-factor-desc">{factor.description}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default RiskDashboard;
