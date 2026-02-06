/**
 * VENDOR DETAIL PAGE
 *
 * WHAT IT DOES:
 * Shows all information about a SINGLE vendor.
 * Think of this as the vendor's "profile page."
 *
 * KEY CONCEPT: URL PARAMETERS
 * The URL /vendors/42 has "42" as a parameter.
 * We use React Router's useParams() hook to extract it,
 * then fetch that specific vendor from the backend.
 *
 * HOW IT FITS IN:
 * User clicks vendor name in VendorList -> navigates to /vendors/{id} -> this page loads
 */

import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { Vendor } from '../types/vendor';
import { getVendor, deleteVendor } from '../services/api';

function VendorDetail() {
  const { id } = useParams<{ id: string }>();  // Extract the ID from the URL
  const navigate = useNavigate();               // For programmatic navigation
  const [vendor, setVendor] = useState<Vendor | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;

    async function loadVendor() {
      try {
        setLoading(true);
        const data = await getVendor(Number(id));
        setVendor(data);
      } catch (err) {
        setError('Vendor not found.');
      } finally {
        setLoading(false);
      }
    }

    loadVendor();
  }, [id]);

  async function handleDelete() {
    if (!vendor) return;
    if (!window.confirm(`Are you sure you want to delete "${vendor.name}"?`)) return;

    try {
      await deleteVendor(vendor.id);
      navigate('/vendors');  // Go back to the list after deleting
    } catch (err) {
      setError('Failed to delete vendor.');
    }
  }

  if (loading) return <p>Loading vendor...</p>;
  if (error) return <p style={{ color: 'red' }}>{error}</p>;
  if (!vendor) return <p>Vendor not found.</p>;

  // Helper: display a field or a dash if empty
  const field = (label: string, value: string | null) => (
    <div style={{ marginBottom: '12px' }}>
      <strong>{label}:</strong>{' '}
      <span>{value || '—'}</span>
    </div>
  );

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1>{vendor.name}</h1>
        <div style={{ display: 'flex', gap: '10px' }}>
          <Link
            to={`/vendors/${vendor.id}/edit`}
            style={{
              padding: '8px 16px',
              backgroundColor: '#0066cc',
              color: 'white',
              textDecoration: 'none',
              borderRadius: '5px',
            }}
          >
            Edit
          </Link>
          <button
            onClick={handleDelete}
            style={{
              padding: '8px 16px',
              backgroundColor: '#cc0000',
              color: 'white',
              border: 'none',
              borderRadius: '5px',
              cursor: 'pointer',
            }}
          >
            Delete
          </button>
        </div>
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: '1fr 1fr',
        gap: '20px',
        marginTop: '20px',
        padding: '20px',
        backgroundColor: '#f9f9f9',
        borderRadius: '8px',
      }}>
        <div>
          <h3 style={{ marginTop: 0 }}>Contact Information</h3>
          {field('Email', vendor.email)}
          {field('Phone', vendor.phone)}
          {field('Website', vendor.website)}
        </div>

        <div>
          <h3 style={{ marginTop: 0 }}>Business Details</h3>
          {field('Category', vendor.category)}
          {field('Tax ID', vendor.tax_id)}
          {field('Status', vendor.status)}
        </div>

        <div>
          <h3 style={{ marginTop: 0 }}>Address</h3>
          {field('Address', vendor.address)}
          {field('City', vendor.city)}
          {field('State', vendor.state)}
          {field('Zip Code', vendor.zip_code)}
          {field('Country', vendor.country)}
        </div>

        <div>
          <h3 style={{ marginTop: 0 }}>Description</h3>
          <p>{vendor.description || 'No description provided.'}</p>
        </div>
      </div>

      <div style={{ marginTop: '20px', color: '#888', fontSize: '14px' }}>
        <p>Created: {new Date(vendor.created_at).toLocaleDateString()}</p>
        <p>Last updated: {new Date(vendor.updated_at).toLocaleDateString()}</p>
      </div>

      <Link to="/vendors" style={{ display: 'inline-block', marginTop: '20px', color: '#0066cc' }}>
        &larr; Back to all vendors
      </Link>
    </div>
  );
}

export default VendorDetail;
