/**
 * VENDOR FORM PAGE (Create & Edit)
 *
 * WHAT IT DOES:
 * A form for creating a new vendor OR editing an existing one.
 * The same component handles both -- this is called "component reuse."
 *
 * HOW IT KNOWS WHICH MODE:
 * - URL is /vendors/new     -> no ID in URL -> CREATE mode
 * - URL is /vendors/42/edit -> ID is 42     -> EDIT mode (loads existing data)
 *
 * WALKTHROUGH: WHAT HAPPENS WHEN YOU CLICK "CREATE VENDOR":
 *
 *   1. User fills out form fields (each keystroke updates React state)
 *   2. User clicks "Create Vendor" button
 *   3. handleSubmit() fires, which:
 *      a. Prevents the browser from reloading the page
 *      b. Validates required fields (name, email)
 *      c. Calls createVendor() from api.ts
 *   4. api.ts sends HTTP POST to http://localhost:8000/api/vendors/
 *   5. Backend validates data, saves to PostgreSQL, returns new vendor
 *   6. On success, React navigates to /vendors (the list page)
 *   7. VendorList loads and shows the new vendor in the table
 *
 * KEY CONCEPT - CONTROLLED INPUTS:
 * Every form field's value is stored in React state (formData).
 * Every keystroke calls handleChange() which updates state.
 * React then re-renders the input with the new value.
 * This gives us full control: we can validate, format, or block input.
 */

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { VendorCreate } from '../types/vendor';
import { createVendor, getVendor, updateVendor } from '../services/api';

function VendorForm() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const isEditing = Boolean(id);

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
  const [success, setSuccess] = useState<string | null>(null);

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
  // This SINGLE function handles ALL inputs. It reads the input's "name"
  // attribute and updates the matching key in formData.
  function handleChange(e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    // Clear any previous error when the user starts typing
    if (error) setError(null);
  }

  // Handle form submission
  async function handleSubmit(e: React.FormEvent) {
    // e.preventDefault() stops the browser from reloading the page.
    // Without this, the browser would do a traditional form POST
    // and our React app would restart from scratch.
    e.preventDefault();

    // --- VALIDATION ---
    // Check required fields before sending to the backend.
    // The backend also validates, but checking here gives instant feedback.
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
        setSuccess('Vendor updated successfully!');
      } else {
        await createVendor(formData);
        setSuccess('Vendor created successfully!');
      }

      // Brief pause so the user sees the success message, then navigate
      setTimeout(() => navigate('/vendors'), 800);
    } catch (err) {
      setError(`Failed to ${isEditing ? 'update' : 'create'} vendor. Please try again.`);
    } finally {
      setSaving(false);
    }
  }

  // Helper: generates a form input field.
  // This avoids repeating the same HTML structure for every field.
  const inputField = (label: string, name: string, required = false, type = 'text') => (
    <div className="form-group">
      <label>
        {label}{required && ' *'}
      </label>
      <input
        type={type}
        name={name}
        value={(formData as Record<string, string>)[name] || ''}
        onChange={handleChange}
        required={required}
      />
    </div>
  );

  return (
    <div className="form-container">
      <div className="page-header">
        <h1>{isEditing ? 'Edit Vendor' : 'Add New Vendor'}</h1>
      </div>

      {error && <div className="alert alert-error">{error}</div>}
      {success && <div className="alert alert-success">{success}</div>}

      <form onSubmit={handleSubmit}>
        {/* --- BASIC INFORMATION --- */}
        <div className="form-section">
          <h3>Basic Information</h3>
          {inputField('Company Name', 'name', true)}
          {inputField('Email', 'email', true, 'email')}
          {inputField('Phone', 'phone')}
          {inputField('Website', 'website', false, 'url')}
        </div>

        {/* --- BUSINESS DETAILS --- */}
        <div className="form-section">
          <h3>Business Details</h3>
          <div className="form-group">
            <label>Category</label>
            <select
              name="category"
              value={formData.category || ''}
              onChange={handleChange}
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

          <div className="form-group">
            <label>Description</label>
            <textarea
              name="description"
              value={formData.description || ''}
              onChange={handleChange}
              rows={4}
            />
          </div>
        </div>

        {/* --- ADDRESS --- */}
        <div className="form-section">
          <h3>Address</h3>
          {inputField('Street Address', 'address')}
          <div className="form-row">
            {inputField('City', 'city')}
            {inputField('State', 'state')}
          </div>
          <div className="form-row">
            {inputField('Zip Code', 'zip_code')}
            {inputField('Country', 'country')}
          </div>
        </div>

        {/* --- SUBMIT BUTTONS --- */}
        <div className="form-actions">
          <button type="submit" disabled={saving} className="btn btn-primary btn-lg">
            {saving ? 'Saving...' : (isEditing ? 'Update Vendor' : 'Create Vendor')}
          </button>
          <Link to="/vendors" className="btn btn-secondary btn-lg">
            Cancel
          </Link>
        </div>
      </form>
    </div>
  );
}

export default VendorForm;
