/**
 * SPEND ANALYTICS DASHBOARD (Now with Multi-Currency!)
 * =====================================================
 * This page shows financial insights about vendor spending.
 *
 * IT HAS FOUR SECTIONS:
 * 1. Summary Cards — Grand totals (total spent, vendor count, avg payment)
 * 2. Monthly Spending Chart — Bar chart showing spending over time
 * 3. Spend by Vendor — Horizontal bars showing who we spend the most with
 * 4. Recent Payments — A table of the latest payment records
 *
 * MULTI-CURRENCY FEATURE:
 * Since we work with EMEA vendors, payments come in different currencies
 * (USD, EUR, GBP). The analytics dashboard converts all amounts to one
 * display currency so you can compare apples to apples.
 *
 * Think of it like a travel expense report: you paid hotels in GBP,
 * taxis in EUR, and flights in USD. To see your "total trip cost,"
 * you need to convert everything to one currency first.
 *
 * The currency switcher at the top lets you choose which currency
 * to view everything in — like clicking "Show prices in EUR"
 * on an international shopping website.
 */

import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell, PieChart, Pie,
} from 'recharts';
import { SpendSummary, VendorSpendSummary, MonthlySpend, Payment } from '../types/payment';
import {
  getSpendSummary,
  getSpendByVendor,
  getMonthlySpend,
  getPayments,
  updateCurrencyPreference,
} from '../services/api';
import { useAuth } from '../context/AuthContext';

// Colors for the vendor pie chart slices
const CHART_COLORS = [
  '#0066cc', '#28a745', '#fd7e14', '#dc3545', '#6f42c1',
  '#20c997', '#e83e8c', '#17a2b8', '#ffc107', '#6c757d',
];

// Currency symbols for display
const CURRENCY_SYMBOLS: Record<string, string> = {
  USD: '$',
  EUR: '\u20ac',
  GBP: '\u00a3',
};

function SpendAnalytics() {
  const { user } = useAuth();

  // --- STATE ---
  const [summary, setSummary] = useState<SpendSummary | null>(null);
  const [vendorSpend, setVendorSpend] = useState<VendorSpendSummary[]>([]);
  const [monthlySpend, setMonthlySpend] = useState<MonthlySpend[]>([]);
  const [recentPayments, setRecentPayments] = useState<Payment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // The currently selected display currency
  const [displayCurrency, setDisplayCurrency] = useState(
    user?.preferred_currency || 'USD'
  );

  // --- LOAD DATA ---
  useEffect(() => {
    loadAnalytics();
  }, [displayCurrency]); // Reload when currency changes

  async function loadAnalytics() {
    try {
      setLoading(true);
      const [summaryData, vendorData, monthlyData, paymentsData] = await Promise.all([
        getSpendSummary(displayCurrency),
        getSpendByVendor(displayCurrency),
        getMonthlySpend(undefined, displayCurrency),
        getPayments(),
      ]);
      setSummary(summaryData);
      setVendorSpend(vendorData);
      setMonthlySpend(monthlyData);
      setRecentPayments(paymentsData);
    } catch (err) {
      setError('Failed to load analytics data');
    } finally {
      setLoading(false);
    }
  }

  // When user switches the display currency
  async function handleCurrencyChange(newCurrency: string) {
    setDisplayCurrency(newCurrency);
    // Also save preference to backend so it persists across sessions
    try {
      await updateCurrencyPreference(newCurrency);
    } catch {
      // Non-critical: preference just won't persist
    }
  }

  // --- HELPERS ---
  /**
   * Format a number as currency.
   *
   * Intl.NumberFormat is a built-in browser API that knows how to format
   * numbers for different locales and currencies. It handles:
   * - The right symbol ($, €, £)
   * - The right position (€100 vs $100 vs 100£)
   * - Thousands separators (1,000 vs 1.000)
   */
  function formatCurrency(value: number): string {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: displayCurrency,
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  }

  function formatDate(dateStr: string): string {
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  }

  /**
   * Format a payment amount with its ORIGINAL currency.
   * Used in the recent payments table where each row may be in a different currency.
   */
  function formatPaymentAmount(amount: number, currency: string): string {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency || 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  }

  // Custom tooltip for the monthly chart
  function MonthlyTooltip({ active, payload, label }: any) {
    if (active && payload && payload.length) {
      return (
        <div className="chart-tooltip">
          <p><strong>{label}</strong></p>
          <p>Spent: {formatCurrency(payload[0].value)}</p>
          <p>Payments: {payload[0].payload.payment_count}</p>
        </div>
      );
    }
    return null;
  }

  const symbol = CURRENCY_SYMBOLS[displayCurrency] || displayCurrency;

  if (loading) return <div className="loading">Loading analytics...</div>;

  return (
    <div>
      {/* --- PAGE HEADER with Currency Switcher --- */}
      <div className="page-header">
        <h1>Spend Analytics</h1>
        <div className="page-header-actions">
          {/* Currency Switcher — like "Show prices in EUR" on a website */}
          <div className="currency-switcher">
            <label>Display in:</label>
            {['USD', 'EUR', 'GBP'].map((code) => (
              <button
                key={code}
                className={`currency-btn ${displayCurrency === code ? 'currency-btn-active' : ''}`}
                onClick={() => handleCurrencyChange(code)}
              >
                {CURRENCY_SYMBOLS[code]} {code}
              </button>
            ))}
          </div>
          <Link to="/payments/new" className="btn btn-primary">
            + Add Payment
          </Link>
        </div>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {/* --- SUMMARY CARDS --- */}
      {summary && (
        <div className="stats-row" style={{ gridTemplateColumns: 'repeat(4, 1fr)' }}>
          <div className="stat-card stat-total">
            <div className="stat-number">{formatCurrency(summary.total_spent)}</div>
            <div className="stat-label">Total Spent ({displayCurrency})</div>
          </div>
          <div className="stat-card stat-attention">
            <div className="stat-number">{summary.payment_count}</div>
            <div className="stat-label">Total Payments</div>
          </div>
          <div className="stat-card" style={{ borderTopColor: '#6f42c1' }}>
            <div className="stat-number" style={{ color: '#6f42c1' }}>
              {formatCurrency(summary.average_payment)}
            </div>
            <div className="stat-label">Average Payment ({displayCurrency})</div>
          </div>
          <div className="stat-card" style={{ borderTopColor: '#20c997' }}>
            <div className="stat-number" style={{ color: '#20c997' }}>
              {summary.vendor_count}
            </div>
            <div className="stat-label">Vendors Paid</div>
          </div>
        </div>
      )}

      {/* --- MONTHLY SPENDING CHART --- */}
      <div className="card" style={{ marginBottom: '24px' }}>
        <h3>Monthly Spending ({displayCurrency})</h3>
        {monthlySpend.length === 0 ? (
          <p className="text-muted">No payment data yet. Add payments to see the chart.</p>
        ) : (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={monthlySpend}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis
                dataKey="month_name"
                tick={{ fontSize: 12 }}
                tickFormatter={(name: string) => name.substring(0, 3)}
              />
              <YAxis
                tick={{ fontSize: 12 }}
                tickFormatter={(value: number) => `${symbol}${(value / 1000).toFixed(0)}k`}
              />
              <Tooltip content={<MonthlyTooltip />} />
              <Bar dataKey="total_spent" fill="#0066cc" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* --- TWO-COLUMN LAYOUT: Vendor Spend + Recent Payments --- */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>

        {/* --- SPEND BY VENDOR (Pie Chart) --- */}
        <div className="card">
          <h3>Spend by Vendor ({displayCurrency})</h3>
          {vendorSpend.length === 0 ? (
            <p className="text-muted">No vendor spending data yet.</p>
          ) : (
            <>
              <ResponsiveContainer width="100%" height={250}>
                <PieChart>
                  <Pie
                    data={vendorSpend}
                    dataKey="total_spent"
                    nameKey="vendor_name"
                    cx="50%"
                    cy="50%"
                    outerRadius={90}
                    label={({ vendor_name, percent }: any) =>
                      `${vendor_name} (${(percent * 100).toFixed(0)}%)`
                    }
                    labelLine={true}
                  >
                    {vendorSpend.map((_entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={CHART_COLORS[index % CHART_COLORS.length]}
                      />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value: number) => formatCurrency(value)} />
                </PieChart>
              </ResponsiveContainer>

              {/* Vendor spend table below the chart */}
              <table className="data-table" style={{ marginTop: '16px' }}>
                <thead>
                  <tr>
                    <th>Vendor</th>
                    <th>Total Spent ({displayCurrency})</th>
                    <th>Payments</th>
                  </tr>
                </thead>
                <tbody>
                  {vendorSpend.map(v => (
                    <tr key={v.vendor_id}>
                      <td>
                        <Link to={`/vendors/${v.vendor_id}`}>{v.vendor_name}</Link>
                      </td>
                      <td>{formatCurrency(v.total_spent)}</td>
                      <td>{v.payment_count}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </>
          )}
        </div>

        {/* --- RECENT PAYMENTS TABLE --- */}
        <div className="card">
          <h3>Recent Payments</h3>
          {recentPayments.length === 0 ? (
            <div className="empty-state" style={{ padding: '30px' }}>
              <p>No payments recorded yet.</p>
              <Link to="/payments/new" className="btn btn-primary">
                Add First Payment
              </Link>
            </div>
          ) : (
            <table className="data-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Vendor</th>
                  <th>Amount</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {recentPayments.slice(0, 10).map(p => (
                  <tr key={p.id}>
                    <td>{formatDate(p.payment_date)}</td>
                    <td>{p.vendor_name || '\u2014'}</td>
                    <td>
                      <strong>{formatPaymentAmount(p.amount, p.currency)}</strong>
                    </td>
                    <td>
                      <span className={`status-badge status-${p.status === 'paid' ? 'active' : p.status === 'pending' ? 'pending' : 'inactive'}`}>
                        {p.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}

export default SpendAnalytics;
