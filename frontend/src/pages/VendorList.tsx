/**
 * VENDOR LIST PAGE
 *
 * WHAT IT DOES:
 * Shows a table of all vendors. This is the main "dashboard" page.
 * Users can see all vendors at a glance, click to view details,
 * or delete a vendor.
 *
 * KEY REACT CONCEPTS USED HERE:
 *
 * 1. useState: Stores data that can change (like the list of vendors).
 *    When the data changes, React automatically re-renders the page.
 *
 * 2. useEffect: Runs code when the component first appears on screen.
 *    We use it to fetch vendors from the backend when the page loads.
 *
 * 3. Conditional rendering: Showing different things based on state
 *    (loading spinner vs. data vs. error message).
 */

import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Vendor } from '../types/vendor';
import { getVendors, deleteVendor } from '../services/api';

function VendorList() {
  // --- STATE ---
  // Think of state as "variables that React watches."
  // When these change, the page automatically updates.
  const [vendors, setVendors] = useState<Vendor[]>([]);  // The list of vendors
  const [loading, setLoading] = useState(true);           // Are we still loading?
  const [error, setError] = useState<string | null>(null); // Any error message

  // --- LOAD DATA ON PAGE OPEN ---
  // useEffect with [] runs ONCE when the component first appears.
  useEffect(() => {
    loadVendors();
  }, []);

  async function loadVendors() {
    try {
      setLoading(true);
      const data = await getVendors();  // Calls our API service
      setVendors(data);
      setError(null);
    } catch (err) {
      setError('Failed to load vendors. Is the backend running?');
    } finally {
      setLoading(false);
    }
  }

  async function handleDelete(id: number, name: string) {
    // Confirm before deleting -- prevents accidental clicks
    if (!window.confirm(`Are you sure you want to delete "${name}"?`)) {
      return;
    }
    try {
      await deleteVendor(id);
      // Remove the vendor from our local list without re-fetching
      setVendors(vendors.filter(v => v.id !== id));
    } catch (err) {
      setError('Failed to delete vendor.');
    }
  }

  // --- RENDER ---
  // Show loading state
  if (loading) {
    return <p>Loading vendors...</p>;
  }

  // Show error state
  if (error) {
    return (
      <div>
        <p style={{ color: 'red' }}>{error}</p>
        <button onClick={loadVendors}>Try Again</button>
      </div>
    );
  }

  // Show the vendor table
  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h1>Vendors</h1>
        <Link
          to="/vendors/new"
          style={{
            padding: '10px 20px',
            backgroundColor: '#0066cc',
            color: 'white',
            textDecoration: 'none',
            borderRadius: '5px',
          }}
        >
          + Add Vendor
        </Link>
      </div>

      {vendors.length === 0 ? (
        <p>No vendors yet. Click "Add Vendor" to create your first one.</p>
      ) : (
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ borderBottom: '2px solid #e0e0e0', textAlign: 'left' }}>
              <th style={{ padding: '12px 8px' }}>Name</th>
              <th style={{ padding: '12px 8px' }}>Category</th>
              <th style={{ padding: '12px 8px' }}>Email</th>
              <th style={{ padding: '12px 8px' }}>Status</th>
              <th style={{ padding: '12px 8px' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {vendors.map((vendor) => (
              <tr key={vendor.id} style={{ borderBottom: '1px solid #f0f0f0' }}>
                <td style={{ padding: '12px 8px' }}>
                  <Link to={`/vendors/${vendor.id}`} style={{ color: '#0066cc' }}>
                    {vendor.name}
                  </Link>
                </td>
                <td style={{ padding: '12px 8px' }}>{vendor.category || '—'}</td>
                <td style={{ padding: '12px 8px' }}>{vendor.email}</td>
                <td style={{ padding: '12px 8px' }}>
                  <span style={{
                    padding: '4px 8px',
                    borderRadius: '12px',
                    fontSize: '12px',
                    fontWeight: 'bold',
                    backgroundColor: vendor.status === 'active' ? '#d4edda' :
                                     vendor.status === 'approved' ? '#cce5ff' :
                                     vendor.status === 'pending' ? '#fff3cd' :
                                     vendor.status === 'rejected' ? '#f8d7da' : '#e2e3e5',
                    color: vendor.status === 'active' ? '#155724' :
                           vendor.status === 'approved' ? '#004085' :
                           vendor.status === 'pending' ? '#856404' :
                           vendor.status === 'rejected' ? '#721c24' : '#383d41',
                  }}>
                    {vendor.status}
                  </span>
                </td>
                <td style={{ padding: '12px 8px' }}>
                  <Link to={`/vendors/${vendor.id}/edit`} style={{ marginRight: '10px', color: '#0066cc' }}>
                    Edit
                  </Link>
                  <button
                    onClick={() => handleDelete(vendor.id, vendor.name)}
                    style={{
                      background: 'none',
                      border: 'none',
                      color: '#cc0000',
                      cursor: 'pointer',
                    }}
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
