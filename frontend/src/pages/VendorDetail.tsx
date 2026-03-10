/**
 * VENDOR DETAIL PAGE
 *
 * WHAT IT DOES:
 * Shows all information about a SINGLE vendor -- their "profile page."
 * Also shows all CONTRACTS associated with this vendor.
 *
 * KEY CONCEPT: URL PARAMETERS
 * The URL /vendors/42 has "42" as a parameter.
 * We use React Router's useParams() to extract it,
 * then fetch that specific vendor from the backend.
 *
 * NEW CONCEPT: PARALLEL API CALLS WITH Promise.all
 * This page needs TWO pieces of data: vendor info AND contracts.
 * Instead of fetching one then the other (slow), we fetch BOTH
 * at the same time using Promise.all(). Think of it like ordering
 * your appetizer and main course simultaneously instead of waiting
 * for the appetizer to arrive before ordering the main course.
 *
 * HOW IT FITS IN:
 * User clicks vendor name in VendorList -> /vendors/{id} -> this page
 */

import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { Vendor } from '../types/vendor';
import { Contract } from '../types/contract';
import { getVendor, deleteVendor, getVendorContracts, deleteContract } from '../services/api';

// Build the full URL for downloading uploaded documents.
// document_url from the backend is a relative path like "/uploads/contracts/abc.pdf"
// We need to prepend the backend base URL so the browser can fetch it.
const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Maps a status string to a CSS class name
function statusClass(status: string): string {
  const map: Record<string, string> = {
    active: 'status-active',
    approved: 'status-approved',
    pending: 'status-pending',
    rejected: 'status-rejected',
    inactive: 'status-inactive',
    draft: 'status-pending',
    expired: 'status-inactive',
    terminated: 'status-rejected',
  };
  return map[status] || 'status-inactive';
}

function VendorDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [vendor, setVendor] = useState<Vendor | null>(null);
  const [contracts, setContracts] = useState<Contract[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;

    async function loadData() {
      try {
        setLoading(true);
        // Promise.all runs BOTH requests simultaneously.
        // Much faster than: const vendor = await getVendor(); const contracts = await getContracts();
        const [vendorData, contractsData] = await Promise.all([
          getVendor(Number(id)),
          getVendorContracts(Number(id)),
        ]);
        setVendor(vendorData);
        setContracts(contractsData);
      } catch (err) {
        setError('Vendor not found.');
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, [id]);

  async function handleDelete() {
    if (!vendor) return;
    if (!window.confirm(`Are you sure you want to delete "${vendor.name}"?`)) return;

    try {
      await deleteVendor(vendor.id);
      navigate('/vendors');
    } catch (err) {
      setError('Failed to delete vendor.');
    }
  }

  if (loading) return <div className="loading">Loading vendor...</div>;
  if (error) return <div className="alert alert-error">{error}</div>;
  if (!vendor) return <div className="alert alert-error">Vendor not found.</div>;

  // Helper: display a labeled field or a dash if empty
  const field = (label: string, value: string | null) => (
    <div className="detail-field">
      <strong>{label}:</strong>
      <span>{value || '—'}</span>
    </div>
  );

  return (
    <div>
      {/* --- HEADER with title and action buttons --- */}
      <div className="page-header">
        <h1>{vendor.name}</h1>
        <div style={{ display: 'flex', gap: '10px' }}>
          <Link to={`/vendors/${vendor.id}/edit`} className="btn btn-primary">
            Edit
          </Link>
          <button onClick={handleDelete} className="btn btn-danger">
            Delete
          </button>
        </div>
      </div>

      {/* --- STATUS BADGE --- */}
      <span className={`status-badge ${statusClass(vendor.status)}`}>
        {vendor.status}
      </span>

      {/* --- DETAIL CARDS in a 2-column grid --- */}
      <div className="detail-grid">
        <div className="card">
          <h3>Contact Information</h3>
          {field('Email', vendor.email)}
          {field('Phone', vendor.phone)}
          {field('Website', vendor.website)}
        </div>

        <div className="card">
          <h3>Business Details</h3>
          {field('Category', vendor.category)}
          {field('Tax ID', vendor.tax_id)}
        </div>

        <div className="card">
          <h3>Address</h3>
          {field('Street', vendor.address)}
          {field('City', vendor.city)}
          {field('State', vendor.state)}
          {field('Zip Code', vendor.zip_code)}
          {field('Country', vendor.country)}
        </div>

        <div className="card">
          <h3>Description</h3>
          <p style={{ margin: 0, color: vendor.description ? '#333' : '#999' }}>
            {vendor.description || 'No description provided.'}
          </p>
        </div>
      </div>

      {/* --- CONTRACTS SECTION ---
          Shows all contracts linked to this vendor.
          Includes: Add button, download links, delete buttons. */}
      <div style={{ marginTop: '32px' }}>
        <div className="page-header">
          <h2 style={{ margin: 0 }}>Contracts ({contracts.length})</h2>
          <Link to={`/vendors/${vendor.id}/contracts/new`} className="btn btn-primary btn-sm">
            + Add Contract
          </Link>
        </div>

        {contracts.length === 0 ? (
          <div className="card" style={{ textAlign: 'center', color: '#888', marginTop: '12px' }}>
            <p>No contracts with this vendor yet.</p>
            <Link to={`/vendors/${vendor.id}/contracts/new`} className="btn btn-primary">
              + Add First Contract
            </Link>
          </div>
        ) : (
          <table className="data-table" style={{ marginTop: '12px' }}>
            <thead>
              <tr>
                <th>Title</th>
                <th>Value</th>
                <th>Dates</th>
                <th>Status</th>
                <th>Document</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {contracts.map((contract) => (
                <tr key={contract.id}>
                  <td>
                    <strong>{contract.title}</strong>
                    {contract.contract_number && (
                      <div style={{ fontSize: '12px', color: '#888' }}>{contract.contract_number}</div>
                    )}
                  </td>
                  <td>{contract.value ? `$${contract.value.toLocaleString()}` : '—'}</td>
                  <td style={{ fontSize: '13px' }}>
                    {contract.start_date || '—'} to {contract.end_date || '—'}
                  </td>
                  <td>
                    <span className={`status-badge ${statusClass(contract.status)}`}>
                      {contract.status}
                    </span>
                  </td>
                  <td>
                    {contract.document_url ? (
                      <a
                        href={`${API_BASE}${contract.document_url}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-link"
                      >
                        Download
                      </a>
                    ) : (
                      <span style={{ color: '#999', fontSize: '13px' }}>None</span>
                    )}
                  </td>
                  <td>
                    <button
                      onClick={async () => {
                        if (!window.confirm(`Delete contract "${contract.title}"?`)) return;
                        try {
                          await deleteContract(contract.id);
                          setContracts(contracts.filter(c => c.id !== contract.id));
                        } catch {
                          setError('Failed to delete contract.');
                        }
                      }}
                      className="text-link text-danger"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* --- FOOTER --- */}
      <div className="timestamps">
        <p>Created: {new Date(vendor.created_at).toLocaleDateString()}</p>
        <p>Last updated: {new Date(vendor.updated_at).toLocaleDateString()}</p>
      </div>

      <Link to="/vendors" className="back-link">
        &larr; Back to all vendors
      </Link>
    </div>
  );
}

export default VendorDetail;
