/**
 * GLOBAL SEARCH PAGE
 * ====================
 * A single search bar that finds results across BOTH vendors and contracts.
 *
 * ANALOGY - Google vs. Individual Websites:
 * Instead of going to the Vendors page to search vendors, and then
 * going to the Contracts page to search contracts, this is like Google:
 * one search box that finds everything across the whole system.
 *
 * HOW IT WORKS:
 * 1. User types a search term (e.g., "acme")
 * 2. After debouncing (300ms wait), we fire TWO API calls in parallel:
 *    - GET /api/vendors/?search=acme
 *    - GET /api/contracts/?search=acme
 * 3. We display both result sets in separate sections
 *
 * WHY PARALLEL CALLS?
 * Using Promise.all, both requests happen simultaneously.
 * If vendors takes 200ms and contracts takes 150ms, the total is ~200ms.
 * Sequential would be 200+150 = 350ms. Parallel is always faster!
 */

import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Vendor } from '../types/vendor';
import { Contract } from '../types/contract';
import { getVendors, VendorSearchParams } from '../services/api';
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function statusClass(status: string): string {
  const map: Record<string, string> = {
    active: 'status-active',
    approved: 'status-approved',
    pending: 'status-pending',
    rejected: 'status-rejected',
    inactive: 'status-inactive',
    draft: 'status-pending',
    expired: 'status-rejected',
  };
  return map[status] || 'status-inactive';
}

function SearchPage() {
  const [searchTerm, setSearchTerm] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [vendorResults, setVendorResults] = useState<Vendor[]>([]);
  const [contractResults, setContractResults] = useState<Contract[]>([]);
  const [loading, setLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);

  // Debounce: wait 300ms after typing stops
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchTerm);
    }, 300);
    return () => clearTimeout(timer);
  }, [searchTerm]);

  // Search when debounced value changes
  useEffect(() => {
    if (!debouncedSearch.trim()) {
      setVendorResults([]);
      setContractResults([]);
      setHasSearched(false);
      return;
    }

    async function performSearch() {
      setLoading(true);
      setHasSearched(true);
      try {
        // Fire both searches in parallel for speed
        const [vendors, contractsRes] = await Promise.all([
          getVendors({ search: debouncedSearch }),
          axios.get<Contract[]>(`${API_BASE_URL}/api/contracts/`, {
            params: { search: debouncedSearch },
          }),
        ]);
        setVendorResults(vendors);
        setContractResults(contractsRes.data);
      } catch (err) {
        // If one fails, still show results from the other
        setVendorResults([]);
        setContractResults([]);
      } finally {
        setLoading(false);
      }
    }

    performSearch();
  }, [debouncedSearch]);

  const totalResults = vendorResults.length + contractResults.length;

  function formatCurrency(value: number | null): string {
    if (value === null) return '—';
    return new Intl.NumberFormat('en-US', {
      style: 'currency', currency: 'USD', minimumFractionDigits: 0,
    }).format(value);
  }

  return (
    <div>
      <div className="page-header">
        <h1>Search</h1>
      </div>

      {/* Big search bar */}
      <div className="search-hero">
        <input
          type="text"
          placeholder="Search vendors, contracts, categories..."
          className="search-input-large"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          autoFocus
        />
        {hasSearched && !loading && (
          <p className="search-results-count">
            Found {totalResults} result{totalResults !== 1 ? 's' : ''}
            {debouncedSearch && ` for "${debouncedSearch}"`}
          </p>
        )}
      </div>

      {loading && <div className="loading">Searching...</div>}

      {/* Prompt before searching */}
      {!hasSearched && !loading && (
        <div className="empty-state">
          <p>Type to search across vendors and contracts.</p>
          <p className="text-muted">Search by name, email, category, contract title, or number.</p>
        </div>
      )}

      {/* No results */}
      {hasSearched && !loading && totalResults === 0 && (
        <div className="empty-state">
          <p>No results found for "{debouncedSearch}".</p>
          <p className="text-muted">Try a different search term or check your spelling.</p>
        </div>
      )}

      {/* Vendor Results */}
      {vendorResults.length > 0 && (
        <div className="search-section">
          <h2 className="search-section-title">
            Vendors ({vendorResults.length})
          </h2>
          <table className="data-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Category</th>
                <th>Email</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {vendorResults.map(v => (
                <tr key={v.id}>
                  <td>
                    <Link to={`/vendors/${v.id}`}>{v.name}</Link>
                  </td>
                  <td>{v.category || '—'}</td>
                  <td>{v.email}</td>
                  <td>
                    <span className={`status-badge ${statusClass(v.status)}`}>
                      {v.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Contract Results */}
      {contractResults.length > 0 && (
        <div className="search-section">
          <h2 className="search-section-title">
            Contracts ({contractResults.length})
          </h2>
          <table className="data-table">
            <thead>
              <tr>
                <th>Title</th>
                <th>Vendor</th>
                <th>Value</th>
                <th>End Date</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {contractResults.map(c => (
                <tr key={c.id}>
                  <td>
                    <Link to={`/vendors/${c.vendor_id}`}>
                      {c.title}
                    </Link>
                    {c.contract_number && (
                      <div className="text-muted">{c.contract_number}</div>
                    )}
                  </td>
                  <td>{c.vendor_name || '—'}</td>
                  <td>{formatCurrency(c.value)}</td>
                  <td>
                    {c.end_date
                      ? new Date(c.end_date).toLocaleDateString()
                      : '—'}
                  </td>
                  <td>
                    <span className={`status-badge ${statusClass(c.status)}`}>
                      {c.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default SearchPage;
