/**
 * CONTRACT FORM PAGE
 *
 * WHAT IT DOES:
 * A form for creating a new contract tied to a specific vendor.
 * The vendor_id comes from the URL: /vendors/42/contracts/new
 *
 * USER JOURNEY:
 *   1. User is on VendorDetail page for "Acme Corp"
 *   2. Clicks "+ Add Contract"
 *   3. Lands here with vendor_id=42 pre-filled
 *   4. Fills out contract title, value, dates, etc.
 *   5. Optionally selects a PDF to upload
 *   6. Clicks "Create Contract"
 *   7. Two things happen:
 *      a. Contract is created via POST /api/contracts/
 *      b. If a file was selected, it's uploaded via POST /api/contracts/{id}/upload-document
 *   8. User is redirected back to the vendor's detail page
 *
 * NEW CONCEPT: FILE INPUT
 * The <input type="file"> element lets users pick a file from their computer.
 * We store the selected file in React state. When they submit the form,
 * we first create the contract (to get an ID), then upload the file
 * to that contract ID.
 *
 * WHY TWO STEPS (create then upload)?
 * The create endpoint expects JSON data. The upload endpoint expects
 * multipart/form-data. Mixing them would be complex. Two simple steps
 * is cleaner than one complicated step.
 */

import React, { useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { createContract, uploadContractDocument } from '../services/api';

function ContractForm() {
  // vendor_id comes from the URL: /vendors/:vendorId/contracts/new
  const { vendorId } = useParams<{ vendorId: string }>();
  const navigate = useNavigate();

  // --- FORM STATE ---
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [contractNumber, setContractNumber] = useState('');
  const [value, setValue] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [status, setStatus] = useState('draft');

  // File state: stores the File object the user selected.
  // File is a browser API type that represents a file from the user's computer.
  // It's null until they pick a file.
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Called when the user picks a file using the file input
  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0] || null;

    // Client-side validation (backend also validates, but this is faster)
    if (file) {
      const ext = file.name.split('.').pop()?.toLowerCase();
      const allowedExts = ['pdf', 'doc', 'docx', 'png', 'jpg', 'jpeg'];
      if (!ext || !allowedExts.includes(ext)) {
        setError(`File type .${ext} is not allowed. Use: ${allowedExts.join(', ')}`);
        return;
      }
      if (file.size > 10 * 1024 * 1024) {
        setError('File is too large. Maximum size is 10 MB.');
        return;
      }
    }

    setSelectedFile(file);
    if (error) setError(null);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();

    if (!title.trim()) {
      setError('Contract title is required.');
      return;
    }
    if (!vendorId) {
      setError('No vendor specified.');
      return;
    }

    try {
      setSaving(true);
      setError(null);

      // STEP 1: Create the contract (JSON request)
      const newContract = await createContract({
        title: title.trim(),
        description: description.trim() || undefined,
        contract_number: contractNumber.trim() || undefined,
        vendor_id: Number(vendorId),
        value: value ? parseFloat(value) : undefined,
        start_date: startDate || undefined,
        end_date: endDate || undefined,
        status,
      });

      // STEP 2: If a file was selected, upload it (multipart request)
      // We need the contract ID from step 1, which is why this is sequential.
      if (selectedFile) {
        await uploadContractDocument(newContract.id, selectedFile);
      }

      setSuccess('Contract created successfully!');
      setTimeout(() => navigate(`/vendors/${vendorId}`), 800);
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      setError(detail || 'Failed to create contract. Please try again.');
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="form-container">
      <div className="page-header">
        <h1>Add New Contract</h1>
      </div>

      {error && <div className="alert alert-error">{error}</div>}
      {success && <div className="alert alert-success">{success}</div>}

      <form onSubmit={handleSubmit}>
        {/* --- CONTRACT DETAILS --- */}
        <div className="form-section">
          <h3>Contract Details</h3>

          <div className="form-group">
            <label>Contract Title *</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g., Annual IT Support Agreement"
              required
            />
          </div>

          <div className="form-group">
            <label>Contract Number</label>
            <input
              type="text"
              value={contractNumber}
              onChange={(e) => setContractNumber(e.target.value)}
              placeholder="e.g., CNT-2025-001"
            />
          </div>

          <div className="form-group">
            <label>Description</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
              placeholder="Describe what this contract covers..."
            />
          </div>
        </div>

        {/* --- FINANCIALS & DATES --- */}
        <div className="form-section">
          <h3>Value & Timeline</h3>

          <div className="form-group">
            <label>Contract Value ($)</label>
            <input
              type="number"
              min="0"
              step="0.01"
              value={value}
              onChange={(e) => setValue(e.target.value)}
              placeholder="e.g., 50000"
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Start Date</label>
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
              />
            </div>
            <div className="form-group">
              <label>End Date</label>
              <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
              />
            </div>
          </div>

          <div className="form-group">
            <label>Status</label>
            <select value={status} onChange={(e) => setStatus(e.target.value)}>
              <option value="draft">Draft</option>
              <option value="pending_approval">Pending Approval</option>
              <option value="active">Active</option>
              <option value="expired">Expired</option>
              <option value="terminated">Terminated</option>
            </select>
          </div>
        </div>

        {/* --- FILE UPLOAD SECTION ---
            NEW CONCEPT: <input type="file">
            This creates a "Choose File" button. When the user picks a file,
            handleFileChange fires. We store the File object in state.
            The file isn't uploaded yet -- that happens on form submit. */}
        <div className="form-section">
          <h3>Contract Document</h3>

          <div className="form-group">
            <label>Upload Document (PDF, DOC, or image)</label>
            <input
              type="file"
              accept=".pdf,.doc,.docx,.png,.jpg,.jpeg"
              onChange={handleFileChange}
              className="file-input"
            />
            {selectedFile && (
              <p className="file-selected">
                Selected: {selectedFile.name} ({(selectedFile.size / 1024).toFixed(0)} KB)
              </p>
            )}
          </div>
        </div>

        {/* --- SUBMIT --- */}
        <div className="form-actions">
          <button type="submit" disabled={saving} className="btn btn-primary btn-lg">
            {saving ? 'Creating...' : 'Create Contract'}
          </button>
          <Link to={`/vendors/${vendorId}`} className="btn btn-secondary btn-lg">
            Cancel
          </Link>
        </div>
      </form>
    </div>
  );
}

export default ContractForm;
