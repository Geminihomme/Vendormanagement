/**
 * VENDOR FORM PAGE (Create & Edit)
 *
 * WHAT IT DOES:
 * A form for creating a new vendor OR editing an existing one.
 * The same component handles both cases -- this is called "component reuse."
 *
 * HOW IT KNOWS WHICH MODE:
 * - URL is /vendors/new -> no ID in URL -> CREATE mode
 * - URL is /vendors/42/edit -> ID is 42 -> EDIT mode (loads existing data first)
 *
 * KEY CONCEPTS:
 * - Controlled inputs: React controls the form field values through state.
 *   Every keystroke updates state, and state drives what's displayed.
 *   This gives us full control over validation and formatting.
 *
 * - Form submission: When the user clicks "Save", we call either
 *   createVendor() or updateVendor() from our API service.
 */

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { VendorCreate } from '../types/vendor';
import { createVendor, getVendor, updateVendor } from '../services/api';

function VendorForm() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const isEditing = Boolean(id);  // true if URL has an ID

  // Form state: each field gets its own state variable
  const [formData, setFormData] = useState<VendorCreate>({
    name: '',
    email: '',
    phone: '',
    website: '',
    description: '',
    category: '',
    tax_id: '',
    address: '',
    city: '',
    state: '',
    zip_code: '',
    country: 'US',
  });

  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // If editing, load the existing vendor data into the form
  useEffect(() => {
    if (!id) return;

    async function loadVendor() {
      try {
        const vendor = await getVendor(Number(id));
        setFormData({
          name: vendor.name,
          email: vendor.email,
          phone: vendor.phone || '',
          website: vendor.website || '',
          description: vendor.description || '',
          category: vendor.category || '',
          tax_id: vendor.tax_id || '',
          address: vendor.address || '',
          city: vendor.city || '',
          state: vendor.state || '',
          zip_code: vendor.zip_code || '',
          country: vendor.country || 'US',
        });
      } catch (err) {
        setError('Failed to load vendor for editing.');
      }
    }

    loadVendor();
  }, [id]);

  // Handle form field changes.
  // This single function works for ALL text inputs.
  function handleChange(e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  }

  // Handle form submission
  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();  // Prevent the browser's default form submission (page reload)

    // Basic validation
    if (!formData.name.trim()) {
      setError('Vendor name is required.');
      return;
    }
    if (!formData.email.trim()) {
      setError('Email is required.');
      return;
    }

    try {
      setSaving(true);
      setError(null);

      if (isEditing) {
        await updateVendor(Number(id), formData);
      } else {
        await createVendor(formData);
      }

      navigate('/vendors');  // Go back to the list on success
    } catch (err) {
      setError(`Failed to ${isEditing ? 'update' : 'create'} vendor. Please try again.`);
    } finally {
      setSaving(false);
    }
  }

  // A helper to make form fields less repetitive
  const inputField = (label: string, name: string, required = false, type = 'text') => (
    <div style={{ marginBottom: '16px' }}>
      <label style={{ display: 'block', marginBottom: '4px', fontWeight: 'bold' }}>
        {label}{required && ' *'}
      </label>
      <input
        type={type}
        name={name}
        value={(formData as Record<string, string>)[name] || ''}
        onChange={handleChange}
        required={required}
        style={{
          width: '100%',
          padding: '8px 12px',
          border: '1px solid #ccc',
          borderRadius: '4px',
          fontSize: '14px',
          boxSizing: 'border-box',
        }}
      />
    </div>
  );

  return (
    <div style={{ maxWidth: '700px' }}>
      <h1>{isEditing ? 'Edit Vendor' : 'Add New Vendor'}</h1>

      {error && (
        <div style={{ padding: '12px', backgroundColor: '#f8d7da', color: '#721c24', borderRadius: '4px', marginBottom: '20px' }}>
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <h3>Basic Information</h3>
        {inputField('Company Name', 'name', true)}
        {inputField('Email', 'email', true, 'email')}
        {inputField('Phone', 'phone')}
        {inputField('Website', 'website', false, 'url')}

        <h3>Business Details</h3>
        <div style={{ marginBottom: '16px' }}>
          <label style={{ display: 'block', marginBottom: '4px', fontWeight: 'bold' }}>Category</label>
          <select
            name="category"
            value={formData.category || ''}
            onChange={handleChange}
            style={{
              width: '100%',
              padding: '8px 12px',
              border: '1px solid #ccc',
              borderRadius: '4px',
              fontSize: '14px',
            }}
          >
            <option value="">Select a category</option>
            <option value="IT Services">IT Services</option>
            <option value="Office Supplies">Office Supplies</option>
            <option value="Professional Services">Professional Services</option>
            <option value="Marketing">Marketing</option>
            <option value="Facilities">Facilities</option>
            <option value="Other">Other</option>
          </select>
        </div>
        {inputField('Tax ID', 'tax_id')}

        <div style={{ marginBottom: '16px' }}>
          <label style={{ display: 'block', marginBottom: '4px', fontWeight: 'bold' }}>Description</label>
          <textarea
            name="description"
            value={formData.description || ''}
            onChange={handleChange}
            rows={4}
            style={{
              width: '100%',
              padding: '8px 12px',
              border: '1px solid #ccc',
              borderRadius: '4px',
              fontSize: '14px',
              boxSizing: 'border-box',
            }}
          />
        </div>

        <h3>Address</h3>
        {inputField('Street Address', 'address')}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
          {inputField('City', 'city')}
          {inputField('State', 'state')}
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
          {inputField('Zip Code', 'zip_code')}
          {inputField('Country', 'country')}
        </div>

        <div style={{ display: 'flex', gap: '10px', marginTop: '24px' }}>
          <button
            type="submit"
            disabled={saving}
            style={{
              padding: '10px 24px',
              backgroundColor: '#0066cc',
              color: 'white',
              border: 'none',
              borderRadius: '5px',
              fontSize: '16px',
              cursor: saving ? 'not-allowed' : 'pointer',
              opacity: saving ? 0.7 : 1,
            }}
          >
            {saving ? 'Saving...' : (isEditing ? 'Update Vendor' : 'Create Vendor')}
          </button>
          <button
            type="button"
            onClick={() => navigate('/vendors')}
            style={{
              padding: '10px 24px',
              backgroundColor: '#e0e0e0',
              color: '#333',
              border: 'none',
              borderRadius: '5px',
              fontSize: '16px',
              cursor: 'pointer',
            }}
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}

export default VendorForm;
