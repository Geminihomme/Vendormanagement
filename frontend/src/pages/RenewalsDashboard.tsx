/**
 * RENEWALS DASHBOARD PAGE
 * ========================
 * This is the "bulletin board" that shows all contracts approaching expiration.
 *
 * IT HAS THREE SECTIONS:
 * 1. Summary Cards - Quick stats (how many critical, warning, etc.)
 * 2. Upcoming Renewals Table - All contracts sorted by urgency
 * 3. Notifications Panel - Recent alerts with read/unread status
 *
 * THE "TEST IT NOW" BUTTON:
 * In development, you can click "Run Expiry Check" to manually trigger
 * the same job that normally runs at 8 AM. This lets you test the whole
 * system without waiting. Create a contract with a near-future end date,
 * click the button, and watch notifications appear!
 *
 * HOW URGENCY COLORS WORK:
 * The backend sends an "urgency" field for each contract:
 * - "expired" → red (contract has passed its end date)
 * - "critical" → red (0-30 days left)
 * - "warning" → orange (31-60 days)
 * - "attention" → blue (61-90 days)
 * - "normal" → green (90+ days)
 *
 * We use CSS classes like .urgency-critical to apply these colors.
 */

import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { UpcomingRenewal, Notification } from '../types/notification';
import {
  getUpcomingRenewals,
  getNotifications,
  markNotificationsRead,
  triggerExpiryCheck,
  getUnreadCount,
} from '../services/api';

function RenewalsDashboard() {
  // --- STATE ---
  const [renewals, setRenewals] = useState<UpcomingRenewal[]>([]);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [checkResult, setCheckResult] = useState('');
  const [checking, setChecking] = useState(false);
  const [activeTab, setActiveTab] = useState<'renewals' | 'notifications'>('renewals');

  // --- LOAD DATA ---
  useEffect(() => {
    loadDashboardData();
  }, []);

  async function loadDashboardData() {
    try {
      setLoading(true);
      // Load renewals, notifications, and unread count in parallel
      const [renewalsData, notificationsData, count] = await Promise.all([
        getUpcomingRenewals(),
        getNotifications(),
        getUnreadCount(),
      ]);
      setRenewals(renewalsData);
      setNotifications(notificationsData);
      setUnreadCount(count);
    } catch (err) {
      setError('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  }

  // --- MANUAL TRIGGER (the "Test It Now" button) ---
  async function handleCheckNow() {
    try {
      setChecking(true);
      setCheckResult('');
      const result = await triggerExpiryCheck();

      if (result.new_notifications === 0) {
        setCheckResult('Check complete — no new expiring contracts found.');
      } else {
        setCheckResult(
          `Found ${result.new_notifications} expiring contract(s)! ` +
          `Emails: ${result.email_results.sent} sent, ` +
          `${result.email_results.skipped} skipped (no recipient).`
        );
      }

      // Reload data to show new notifications
      await loadDashboardData();
    } catch (err) {
      setCheckResult('Error running expiry check. Check the console for details.');
    } finally {
      setChecking(false);
    }
  }

  // --- MARK NOTIFICATIONS AS READ ---
  async function handleMarkAllRead() {
    const unreadIds = notifications
      .filter(n => !n.is_read)
      .map(n => n.id);

    if (unreadIds.length === 0) return;

    try {
      await markNotificationsRead(unreadIds);
      await loadDashboardData();
    } catch (err) {
      setError('Failed to mark notifications as read');
    }
  }

  // --- COMPUTE SUMMARY STATS ---
  // These are "derived state" — we compute them from the renewals list
  // instead of storing them separately. This way they're always up to date.
  const stats = {
    expired: renewals.filter(r => r.urgency === 'expired').length,
    critical: renewals.filter(r => r.urgency === 'critical').length,
    warning: renewals.filter(r => r.urgency === 'warning').length,
    attention: renewals.filter(r => r.urgency === 'attention').length,
    total: renewals.length,
  };

  // --- HELPER: Format currency ---
  function formatCurrency(value: number | null): string {
    if (value === null) return '—';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
    }).format(value);
  }

  // --- HELPER: Format date ---
  function formatDate(dateStr: string): string {
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  }

  // --- HELPER: Urgency display ---
  function urgencyLabel(urgency: string): string {
    const labels: Record<string, string> = {
      expired: 'Expired',
      critical: 'Critical',
      warning: 'Warning',
      attention: 'Attention',
      normal: 'On Track',
    };
    return labels[urgency] || urgency;
  }

  if (loading) return <div className="loading">Loading dashboard...</div>;

  return (
    <div>
      {/* --- PAGE HEADER with Test Button --- */}
      <div className="page-header">
        <h1>Contract Renewals Dashboard</h1>
        <button
          className="btn btn-primary"
          onClick={handleCheckNow}
          disabled={checking}
        >
          {checking ? 'Checking...' : 'Run Expiry Check'}
        </button>
      </div>

      {error && <div className="alert alert-error">{error}</div>}
      {checkResult && (
        <div className="alert alert-success">{checkResult}</div>
      )}

      {/* --- SUMMARY CARDS --- */}
      {/* These give you an at-a-glance overview, like a weather dashboard */}
      <div className="stats-row">
        <div className="stat-card stat-expired">
          <div className="stat-number">{stats.expired}</div>
          <div className="stat-label">Expired</div>
        </div>
        <div className="stat-card stat-critical">
          <div className="stat-number">{stats.critical}</div>
          <div className="stat-label">Critical (≤30d)</div>
        </div>
        <div className="stat-card stat-warning">
          <div className="stat-number">{stats.warning}</div>
          <div className="stat-label">Warning (≤60d)</div>
        </div>
        <div className="stat-card stat-attention">
          <div className="stat-number">{stats.attention}</div>
          <div className="stat-label">Attention (≤90d)</div>
        </div>
        <div className="stat-card stat-total">
          <div className="stat-number">{stats.total}</div>
          <div className="stat-label">Total Active</div>
        </div>
      </div>

      {/* --- TAB NAVIGATION --- */}
      <div className="tab-bar">
        <button
          className={`tab-btn ${activeTab === 'renewals' ? 'tab-active' : ''}`}
          onClick={() => setActiveTab('renewals')}
        >
          Upcoming Renewals ({renewals.length})
        </button>
        <button
          className={`tab-btn ${activeTab === 'notifications' ? 'tab-active' : ''}`}
          onClick={() => setActiveTab('notifications')}
        >
          Notifications {unreadCount > 0 && (
            <span className="notification-badge">{unreadCount}</span>
          )}
        </button>
      </div>

      {/* --- RENEWALS TABLE --- */}
      {activeTab === 'renewals' && (
        <div>
          {renewals.length === 0 ? (
            <div className="empty-state">
              <p>No active contracts with end dates found.</p>
              <Link to="/vendors" className="btn btn-primary">
                View Vendors
              </Link>
            </div>
          ) : (
            <table className="data-table">
              <thead>
                <tr>
                  <th>Status</th>
                  <th>Contract</th>
                  <th>Vendor</th>
                  <th>Value</th>
                  <th>End Date</th>
                  <th>Days Left</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {renewals.map(renewal => (
                  <tr key={renewal.contract_id} className={`urgency-row urgency-${renewal.urgency}`}>
                    <td>
                      <span className={`urgency-badge urgency-badge-${renewal.urgency}`}>
                        {urgencyLabel(renewal.urgency)}
                      </span>
                    </td>
                    <td>
                      <strong>{renewal.contract_title}</strong>
                      {renewal.contract_number && (
                        <div className="text-muted">{renewal.contract_number}</div>
                      )}
                    </td>
                    <td>
                      <Link to={`/vendors/${renewal.vendor_id}`}>
                        {renewal.vendor_name}
                      </Link>
                    </td>
                    <td>{formatCurrency(renewal.value)}</td>
                    <td>{formatDate(renewal.end_date)}</td>
                    <td>
                      <strong className={`days-${renewal.urgency}`}>
                        {renewal.days_remaining < 0
                          ? `${Math.abs(renewal.days_remaining)}d overdue`
                          : `${renewal.days_remaining}d`}
                      </strong>
                    </td>
                    <td>
                      <Link
                        to={`/vendors/${renewal.vendor_id}`}
                        className="btn btn-sm btn-secondary"
                      >
                        View
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {/* --- NOTIFICATIONS LIST --- */}
      {activeTab === 'notifications' && (
        <div>
          {notifications.length > 0 && unreadCount > 0 && (
            <div style={{ marginBottom: '16px' }}>
              <button
                className="btn btn-sm btn-secondary"
                onClick={handleMarkAllRead}
              >
                Mark All as Read
              </button>
            </div>
          )}

          {notifications.length === 0 ? (
            <div className="empty-state">
              <p>No notifications yet.</p>
              <p>Click "Run Expiry Check" to scan for expiring contracts.</p>
            </div>
          ) : (
            <div className="notification-list">
              {notifications.map(notif => (
                <div
                  key={notif.id}
                  className={`notification-item ${notif.is_read ? '' : 'notification-unread'}`}
                >
                  <div className="notification-header">
                    <span className={`urgency-badge urgency-badge-${
                      notif.notification_type.includes('30') ? 'critical' :
                      notif.notification_type.includes('60') ? 'warning' :
                      notif.notification_type.includes('90') ? 'attention' :
                      'expired'
                    }`}>
                      {notif.notification_type.replace('_alert', '').replace('_', ' ')}
                    </span>
                    <span className="notification-time">
                      {formatDate(notif.created_at)}
                    </span>
                  </div>
                  <p className="notification-message">{notif.message}</p>
                  <div className="notification-footer">
                    {notif.email_sent && (
                      <span className="notification-email-sent">Email sent</span>
                    )}
                    {notif.contract_id && (
                      <Link to={`/vendors/${notif.contract_id}`} className="text-link">
                        View Contract
                      </Link>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default RenewalsDashboard;
