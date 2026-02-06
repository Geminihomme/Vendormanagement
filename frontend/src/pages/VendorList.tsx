/**
 * VENDOR LIST PAGE
 *
 * WHAT IT DOES:
 * Shows a table of all vendors. This is the main "dashboard" page.
 * Users can search by name, filter by status, and see a count of results.
 *
 * KEY REACT CONCEPTS:
 *
 * 1. useState: Stores data that can change. When state changes,
 *    React automatically re-renders (repaints) the page.
 *    Think of it like a whiteboard -- erase and redraw when data changes.
 *
 * 2. useEffect: Runs code when the component first appears on screen.
 *    We use it to fetch vendors from the backend when the page loads.
 *
 * 3. DERIVED STATE (new concept!):
 *    Instead of storing "filtered vendors" in a separate useState,
 *    we COMPUTE them from the existing state every render.
 *    This is called "derived state" -- data calculated from other data.
 *    It's simpler and can't get out of sync.
 *
 * 4. Conditional rendering: Showing different things based on state
 *    (loading spinner vs. data vs. error message).
 */

import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Vendor } from '../types/vendor';
import { getVendors, deleteVendor } from '../services/api';

// Helper: maps a status string to a CSS class name.
// e.g., "active" -> "status-active" which matches our CSS rule.
function statusClass(status: string): string {
  const map: Record<string, string> = {
    active: 'status-active',
    approved: 'status-approved',
    pending: 'status-pending',
    rejected: 'status-rejected',
    inactive: 'status-inactive',
  };
  return map[status] || 'status-inactive';
}

function VendorList() {
  // --- STATE ---
  // These are the "live variables" React watches. When they change,
  // React repaints the relevant parts of the page automatically.
  const [vendors, setVendors] = useState<Vendor[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');       // Text in the search box
  const [statusFilter, setStatusFilter] = useState('');   // Selected status filter

  // --- DERIVED STATE ---
  // We don't store filtered vendors separately. We compute them on every render.
  // This is SIMPLER and guarantees filtered results are always in sync with
  // the search term and status filter.
  const filteredVendors = vendors.filter((vendor) => {
    const matchesSearch = vendor.name.toLowerCase().includes(searchTerm.toLowerCase())
      || vendor.email.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === '' || vendor.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  // --- LOAD DATA ---
  // useEffect with [] runs ONCE when the component first mounts (appears).
  useEffect(() => {
    loadVendors();
  }, []);

  async function loadVendors() {
    try {
      setLoading(true);
      const data = await getVendors();
      setVendors(data);
      setError(null);
    } catch (err) {
      setError('Failed to load vendors. Is the backend running?');
    } finally {
      setLoading(false);
    }
  }

  async function handleDelete(id: number, name: string) {
    if (!window.confirm(`Are you sure you want to delete "${name}"?`)) {
      return;
    }
    try {
      await deleteVendor(id);
      setVendors(vendors.filter(v => v.id !== id));
    } catch (err) {
      setError('Failed to delete vendor.');
    }
  }

  // --- RENDER: LOADING STATE ---
  if (loading) {
    return <div className="loading">Loading vendors...</div>;
  }

  // --- RENDER: ERROR STATE ---
  if (error) {
    return (
      <div>
        <div className="alert alert-error">{error}</div>
        <button className="btn btn-primary" onClick={loadVendors}>Try Again</button>
      </div>
    );
  }

  // --- RENDER: THE PAGE ---
  return (
    <div>
      {/* Page header: title on left, "Add Vendor" button on right */}
      <div className="page-header">
        <h1>Vendors</h1>
        <Link to="/vendors/new" className="btn btn-primary">
          + Add Vendor
        </Link>
      </div>

      {/* Search & Filter toolbar
          NEW CONCEPT: "Controlled inputs"
          The search box value is controlled by React state (searchTerm).
          Every keystroke updates the state, which re-filters the list instantly.
          This is why typing in the search box filters results in real-time. */}
      {vendors.length > 0 && (
        <div className="toolbar">
          <input
            type="text"
            placeholder="Search by name or email..."
            className="search-input"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
          <select
            className="filter-select"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="">All Statuses</option>
            <option value="pending">Pending</option>
            <option value="approved">Approved</option>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
            <option value="rejected">Rejected</option>
          </select>
          <span className="vendor-count">
            Showing {filteredVendors.length} of {vendors.length} vendors
          </span>
        </div>
      )}

      {/* Empty state -- when there are no vendors at all */}
      {vendors.length === 0 ? (
        <div className="empty-state">
          <p>No vendors yet. Add your first vendor to get started.</p>
          <Link to="/vendors/new" className="btn btn-primary btn-lg">
            + Add Your First Vendor
          </Link>
        </div>
      ) : filteredVendors.length === 0 ? (
        /* No results matching the search/filter */
        <div className="empty-state">
          <p>No vendors match your search.</p>
          <button
            className="btn btn-secondary"
            onClick={() => { setSearchTerm(''); setStatusFilter(''); }}
          >
            Clear Filters
          </button>
        </div>
      ) : (
        /* The vendor table */
        <table className="data-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Category</th>
              <th>Email</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filteredVendors.map((vendor) => (
              <tr key={vendor.id}>
                <td>
                  <Link to={`/vendors/${vendor.id}`}>
                    {vendor.name}
                  </Link>
                </td>
                <td>{vendor.category || '—'}</td>
                <td>{vendor.email}</td>
                <td>
                  <span className={`status-badge ${statusClass(vendor.status)}`}>
                    {vendor.status}
                  </span>
                </td>
                <td>
                  <Link to={`/vendors/${vendor.id}/edit`} className="text-link" style={{ marginRight: '12px' }}>
                    Edit
                  </Link>
                  <button
                    onClick={() => handleDelete(vendor.id, vendor.name)}
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
  );
}

export default VendorList;
