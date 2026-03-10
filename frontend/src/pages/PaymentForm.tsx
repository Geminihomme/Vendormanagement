/**
 * PAYMENT FORM PAGE
 * ===================
 * A form for recording a new payment to a vendor.
 *
 * WHAT IT DOES:
 * 1. Loads the list of vendors (so you can pick who you're paying)
 * 2. Optionally loads contracts for the selected vendor
 * 3. Lets you enter: amount, date, invoice number, description, etc.
 * 4. Submits the payment to the backend
 * 5. Redirects back to the analytics page
 *
 * KEY INTERACTION - VENDOR DROPDOWN CHANGES CONTRACT DROPDOWN:
 * When you pick a vendor, the form loads that vendor's contracts
 * so you can optionally link the payment to a specific contract.
 * This is "cascading dropdowns" — one choice filters the next.
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Vendor } from '../types/vendor';
import { Contract } from '../types/contract';
import { getVendors, getVendorContracts, createPayment } from '../services/api';

function PaymentForm() {
  const navigate = useNavigate();

  // --- FORM STATE ---
  const [vendorId, setVendorId] = useState('');
  const [contractId, setContractId] = useState('');
  const [amount, setAmount] = useState('');
  const [currency, setCurrency] = useState('USD');
  const [paymentDate, setPaymentDate] = useState(
    new Date().toISOString().split('T')[0] // Default to today
  );
  const [invoiceNumber, setInvoiceNumber] = useState('');
  const [description, setDescription] = useState('');
  const [paymentMethod, setPaymentMethod] = useState('');
  const [status, setStatus] = useState('paid');

  // --- DROPDOWN DATA ---
  const [vendors, setVendors] = useState<Vendor[]>([]);
  const [contracts, setContracts] = useState<Contract[]>([]);

  // --- UI STATE ---
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  // Load vendors on mount
  useEffect(() => {
    getVendors()
      .then(setVendors)
      .catch(() => setError('Failed to load vendors'));
  }, []);

  // When vendor changes, load their contracts (cascading dropdown)
  useEffect(() => {
    if (vendorId) {
      setContractId(''); // Reset contract selection
      getVendorContracts(Number(vendorId))
        .then(setContracts)
        .catch(() => setContracts([]));
    } else {
      setContracts([]);
      setContractId('');
    }
  }, [vendorId]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();

    if (!vendorId || !amount || !paymentDate) {
      setError('Vendor, amount, and payment date are required.');
      return;
    }

    try {
      setLoading(true);
      setError('');

      await createPayment({
        vendor_id: Number(vendorId),
        contract_id: contractId ? Number(contractId) : undefined,
        amount: parseFloat(amount),
        currency,
        payment_date: paymentDate,
        invoice_number: invoiceNumber || undefined,
        description: description || undefined,
        payment_method: paymentMethod || undefined,
        status: status,
      });

      setSuccess(true);
      setTimeout(() => navigate('/analytics'), 800);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to record payment');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="form-container">
      <div className="page-header">
        <h1>Record Payment</h1>
      </div>

      {error && <div className="alert alert-error">{error}</div>}
      {success && <div className="alert alert-success">Payment recorded!</div>}

      <form onSubmit={handleSubmit}>
        {/* --- VENDOR & CONTRACT --- */}
        <div className="form-section card">
          <h3>Payment Details</h3>

          <div className="form-group">
            <label>Vendor *</label>
            <select
              value={vendorId}
              onChange={(e) => setVendorId(e.target.value)}
              required
            >
              <option value="">-- Select Vendor --</option>
              {vendors.map(v => (
                <option key={v.id} value={v.id}>{v.name}</option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label>Contract (optional)</label>
            <select
              value={contractId}
              onChange={(e) => setContractId(e.target.value)}
              disabled={!vendorId}
            >
              <option value="">-- No specific contract --</option>
              {contracts.map(c => (
                <option key={c.id} value={c.id}>{c.title}</option>
              ))}
            </select>
          </div>

          <div className="form-row">
            <div className="form-group" style={{ flex: 2 }}>
              <label>Amount *</label>
              <input
                type="number"
                step="0.01"
                min="0.01"
                value={amount}
                onChange={(e) => { setAmount(e.target.value); setError(''); }}
                placeholder="e.g. 5000.00"
                required
              />
            </div>
            <div className="form-group" style={{ flex: 1 }}>
              <label>Currency</label>
              <select value={currency} onChange={(e) => setCurrency(e.target.value)}>
                <option value="USD">USD ($)</option>
                <option value="EUR">EUR (&euro;)</option>
                <option value="GBP">GBP (&pound;)</option>
              </select>
            </div>
            <div className="form-group" style={{ flex: 2 }}>
              <label>Payment Date *</label>
              <input
                type="date"
                value={paymentDate}
                onChange={(e) => setPaymentDate(e.target.value)}
                required
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Invoice Number</label>
              <input
                type="text"
                value={invoiceNumber}
                onChange={(e) => setInvoiceNumber(e.target.value)}
                placeholder="e.g. INV-2026-001"
              />
            </div>
            <div className="form-group">
              <label>Payment Method</label>
              <select
                value={paymentMethod}
                onChange={(e) => setPaymentMethod(e.target.value)}
              >
                <option value="">-- Select --</option>
                <option value="bank_transfer">Bank Transfer</option>
                <option value="check">Check</option>
                <option value="credit_card">Credit Card</option>
                <option value="wire">Wire Transfer</option>
                <option value="other">Other</option>
              </select>
            </div>
          </div>

          <div className="form-group">
            <label>Status</label>
            <select value={status} onChange={(e) => setStatus(e.target.value)}>
              <option value="paid">Paid</option>
              <option value="pending">Pending</option>
              <option value="overdue">Overdue</option>
              <option value="cancelled">Cancelled</option>
            </select>
          </div>

          <div className="form-group">
            <label>Description</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="What was this payment for?"
              rows={3}
            />
          </div>
        </div>

        {/* --- ACTIONS --- */}
        <div className="form-actions">
          <button
            type="submit"
            className="btn btn-primary btn-lg"
            disabled={loading || success}
          >
            {loading ? 'Saving...' : 'Record Payment'}
          </button>
          <button
            type="button"
            className="btn btn-secondary btn-lg"
            onClick={() => navigate('/analytics')}
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}

export default PaymentForm;
