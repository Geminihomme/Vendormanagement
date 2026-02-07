/**
 * VENDOR LIST PAGE (Enhanced with Search, Filters, and Sortable Columns)
 *
 * HOW SEARCH WORKS BEHIND THE SCENES:
 * =====================================
 * Think of searching like finding a book in a library:
 *
 * 1. You type "acme" in the search bar
 * 2. The frontend sends: GET /api/vendors/?search=acme
 * 3. The backend runs: WHERE name LIKE '%acme%' OR email LIKE '%acme%' ...
 * 4. The DATABASE does the heavy lifting (it's optimized for this!)
 * 5. Only matching vendors come back over the network
 *
 * WHY BACKEND SEARCH (not just frontend)?
 * Imagine you have 10,000 vendors. Frontend filtering would require
 * downloading all 10,000 to the browser first — slow and wasteful.
 * Backend search asks the database (which is BUILT for searching)
 * and only sends the 15 matches.
 *
 * DEBOUNCING (The Elevator Analogy):
 * When you type "a-c-m-e" quickly, we don't search after each letter.
 * That would be 4 searches in under a second! Instead, we WAIT 300ms
 * after you stop typing before searching. This is "debouncing."
 *
 * It's like an elevator: the door doesn't close the instant ONE person
 * steps in. It waits a few seconds for more people, THEN closes.
 * Debouncing waits for you to finish typing, THEN searches.
 *
 * SORTABLE COLUMNS:
 * Clicking a column header sorts by that column. Click again to reverse.
 * The arrow (↑/↓) shows which direction. The sorting happens on the
 * backend (ORDER BY name ASC) so it works with any amount of data.
 */

import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { Vendor } from '../types/vendor';
import { getVendors, deleteVendor, getVendorCategories, VendorSearchParams } from '../services/api';

// Helper: maps status to CSS class
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
  const [vendors, setVendors] = useState<Vendor[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Search & Filter state
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [categories, setCategories] = useState<string[]>([]);

  // Sort state
  const [sortBy, setSortBy] = useState('name');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');

  // Debounce state — the actual search value sent to the backend
  const [debouncedSearch, setDebouncedSearch] = useState('');

  // --- DEBOUNCING ---
  // Wait 300ms after the user stops typing before actually searching.
  // This prevents sending a request for every single keystroke.
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchTerm);
    }, 300);

    // Cleanup: if the user types again within 300ms, cancel the previous timer.
    // This is the "elevator door stays open" part.
    return () => clearTimeout(timer);
  }, [searchTerm]);

  // --- LOAD CATEGORIES (once on mount) ---
  useEffect(() => {
    getVendorCategories()
      .then(setCategories)
      .catch(() => {}); // Silently fail — dropdown just won't have categories
  }, []);

  // --- LOAD VENDORS (when any filter/sort changes) ---
  // This runs whenever debouncedSearch, statusFilter, categoryFilter,
  // sortBy, or sortOrder changes. It's the "re-search" trigger.
  const loadVendors = useCallback(async () => {
    try {
      setLoading(true);
      const params: VendorSearchParams = {};

      // Only include parameters that have values
      if (debouncedSearch) params.search = debouncedSearch;
      if (statusFilter) params.status = statusFilter;
      if (categoryFilter) params.category = categoryFilter;
      if (sortBy !== 'name') params.sort_by = sortBy;
      if (sortOrder !== 'asc') params.sort_order = sortOrder;
      // Always send sort params so the backend knows what to do
      params.sort_by = sortBy;
      params.sort_order = sortOrder;

      const data = await getVendors(params);
      setVendors(data);
      setError(null);
    } catch (err) {
      setError('Failed to load vendors. Is the backend running?');
    } finally {
      setLoading(false);
    }
  }, [debouncedSearch, statusFilter, categoryFilter, sortBy, sortOrder]);

  useEffect(() => {
    loadVendors();
  }, [loadVendors]);

  // --- SORT HANDLER ---
  // Click a column header to sort. Click again to reverse direction.
  // Like clicking "Name" in a file explorer to sort alphabetically.
  function handleSort(column: string) {
    if (sortBy === column) {
      // Already sorting by this column — flip the direction
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      // New column — start with ascending
      setSortBy(column);
      setSortOrder('asc');
    }
  }

  // Helper: show sort arrow on the active column
  function sortArrow(column: string): string {
    if (sortBy !== column) return '';
    return sortOrder === 'asc' ? ' ↑' : ' ↓';
  }

  // --- DELETE HANDLER ---
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

  // --- CLEAR ALL FILTERS ---
  function clearFilters() {
    setSearchTerm('');
    setStatusFilter('');
    setCategoryFilter('');
    setSortBy('name');
    setSortOrder('asc');
  }

  const hasActiveFilters = searchTerm || statusFilter || categoryFilter;

  // --- RENDER ---
  return (
    <div>
      {/* Page header */}
      <div className="page-header">
        <h1>Vendors</h1>
        <Link to="/vendors/new" className="btn btn-primary">
          + Add Vendor
        </Link>
      </div>

      {error && (
        <div className="alert alert-error">
          {error}
          <button className="btn btn-sm btn-secondary" onClick={loadVendors} style={{ marginLeft: '12px' }}>
            Try Again
          </button>
        </div>
      )}

      {/* Search & Filter Toolbar */}
      <div className="toolbar">
        <input
          type="text"
          placeholder="Search vendors..."
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
        <select
          className="filter-select"
          value={categoryFilter}
          onChange={(e) => setCategoryFilter(e.target.value)}
        >
          <option value="">All Categories</option>
          {categories.map(cat => (
            <option key={cat} value={cat}>{cat}</option>
          ))}
        </select>
        {hasActiveFilters && (
          <button className="btn btn-sm btn-secondary" onClick={clearFilters}>
            Clear Filters
          </button>
        )}
        <span className="vendor-count">
          {loading ? 'Loading...' : `${vendors.length} vendor${vendors.length !== 1 ? 's' : ''}`}
        </span>
      </div>

      {/* Loading state (overlay so the toolbar stays visible) */}
      {loading && vendors.length === 0 && (
        <div className="loading">Loading vendors...</div>
      )}

      {/* Empty state */}
      {!loading && vendors.length === 0 && !hasActiveFilters && (
        <div className="empty-state">
          <p>No vendors yet. Add your first vendor to get started.</p>
          <Link to="/vendors/new" className="btn btn-primary btn-lg">
            + Add Your First Vendor
          </Link>
        </div>
      )}

      {/* No results for current search */}
      {!loading && vendors.length === 0 && hasActiveFilters && (
        <div className="empty-state">
          <p>No vendors match your search.</p>
          <button className="btn btn-secondary" onClick={clearFilters}>
            Clear Filters
          </button>
        </div>
      )}

      {/* The vendor table with sortable column headers */}
      {vendors.length > 0 && (
        <table className="data-table">
          <thead>
            <tr>
              <th className="sortable-th" onClick={() => handleSort('name')}>
                Name{sortArrow('name')}
              </th>
              <th className="sortable-th" onClick={() => handleSort('category')}>
                Category{sortArrow('category')}
              </th>
              <th className="sortable-th" onClick={() => handleSort('email')}>
                Email{sortArrow('email')}
              </th>
              <th className="sortable-th" onClick={() => handleSort('status')}>
                Status{sortArrow('status')}
              </th>
              <th className="sortable-th" onClick={() => handleSort('created_at')}>
                Added{sortArrow('created_at')}
              </th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {vendors.map((vendor) => (
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
                <td className="text-muted">
                  {new Date(vendor.created_at).toLocaleDateString()}
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
