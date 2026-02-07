/**
 * APPROVAL INBOX PAGE (The Manager's Dashboard)
 * ================================================
 * This is where managers and admins review pending vendor and
 * contract submissions.
 *
 * LAYOUT:
 * 1. Summary stat cards (Pending | Approved | Rejected | Total)
 * 2. Tab bar to filter by status (Pending | Approved | Rejected | All)
 * 3. List of approval cards with Approve/Reject buttons
 * 4. Review modal with comment field
 *
 * THE FLOW:
 * Manager sees "3 Pending" → clicks one → reads details →
 * types a comment → clicks Approve → vendor becomes active →
 * submitter gets an email notification
 */

import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Approval, ApprovalSummary } from '../types/approval';
import {
  getApprovalSummary,
  getPendingApprovals,
  getAllApprovals,
  reviewApproval,
} from '../services/api';

function ApprovalInbox() {
  const { user } = useAuth();

  const [summary, setSummary] = useState<ApprovalSummary>({
    pending: 0, approved: 0, rejected: 0, total: 0,
  });
  const [approvals, setApprovals] = useState<Approval[]>([]);
  const [activeTab, setActiveTab] = useState<string>('pending');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Review modal state
  const [reviewingId, setReviewingId] = useState<number | null>(null);
  const [reviewAction, setReviewAction] = useState<'approve' | 'reject'>('approve');
  const [reviewComment, setReviewComment] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const isManager = user?.role === 'manager' || user?.role === 'admin';

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const [summaryData, approvalsData] = await Promise.all([
        getApprovalSummary(),
        activeTab === 'pending'
          ? getPendingApprovals()
          : activeTab === 'all'
            ? getAllApprovals()
            : getAllApprovals({ status: activeTab }),
      ]);
      setSummary(summaryData);
      setApprovals(approvalsData);
    } catch {
      setError('Failed to load approvals');
    } finally {
      setLoading(false);
    }
  }, [activeTab]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const openReviewModal = (approvalId: number, action: 'approve' | 'reject') => {
    setReviewingId(approvalId);
    setReviewAction(action);
    setReviewComment('');
  };

  const closeReviewModal = () => {
    setReviewingId(null);
    setReviewComment('');
  };

  const handleReview = async () => {
    if (reviewingId === null) return;

    if (reviewAction === 'reject' && !reviewComment.trim()) {
      setError('Please provide a reason for rejection');
      return;
    }

    setSubmitting(true);
    setError('');
    try {
      await reviewApproval(reviewingId, {
        action: reviewAction,
        comment: reviewComment || undefined,
      });
      closeReviewModal();
      loadData(); // Refresh the list
    } catch {
      setError('Failed to submit review');
    } finally {
      setSubmitting(false);
    }
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short', day: 'numeric', year: 'numeric',
      hour: '2-digit', minute: '2-digit',
    });
  };

  if (loading) return <div className="loading">Loading approvals...</div>;

  return (
    <div>
      <div className="page-header">
        <h1>Approval Inbox</h1>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {/* Summary stat cards */}
      <div className="stats-row" style={{ gridTemplateColumns: 'repeat(4, 1fr)' }}>
        <div className={`stat-card stat-warning`}>
          <div className="stat-number">{summary.pending}</div>
          <div className="stat-label">Pending</div>
        </div>
        <div className={`stat-card stat-total`}>
          <div className="stat-number">{summary.approved}</div>
          <div className="stat-label">Approved</div>
        </div>
        <div className={`stat-card stat-expired`}>
          <div className="stat-number">{summary.rejected}</div>
          <div className="stat-label">Rejected</div>
        </div>
        <div className={`stat-card stat-attention`}>
          <div className="stat-number">{summary.total}</div>
          <div className="stat-label">Total</div>
        </div>
      </div>

      {/* Tab bar */}
      <div className="tab-bar">
        {['pending', 'approved', 'rejected', 'all'].map((tab) => (
          <button
            key={tab}
            className={`tab-btn ${activeTab === tab ? 'tab-active' : ''}`}
            onClick={() => setActiveTab(tab)}
          >
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
            {tab === 'pending' && summary.pending > 0 && (
              <span className="notification-badge">{summary.pending}</span>
            )}
          </button>
        ))}
      </div>

      {/* Approval cards list */}
      {approvals.length === 0 ? (
        <div className="empty-state">
          <p>
            {activeTab === 'pending'
              ? 'No pending approvals. All caught up!'
              : `No ${activeTab === 'all' ? '' : activeTab + ' '}approvals found.`}
          </p>
        </div>
      ) : (
        <div className="approval-list">
          {approvals.map((approval) => (
            <div key={approval.id} className={`approval-card approval-${approval.status}`}>
              <div className="approval-card-header">
                <div>
                  <span className={`approval-type-badge approval-type-${approval.approval_type}`}>
                    {approval.approval_type}
                  </span>
                  <span className={`status-badge status-${approval.status}`}>
                    {approval.status}
                  </span>
                </div>
                <span className="text-muted">{formatDate(approval.created_at)}</span>
              </div>

              <h3 className="approval-title">
                <Link
                  to={
                    approval.approval_type === 'vendor'
                      ? `/vendors/${approval.entity_id}`
                      : `/vendors`
                  }
                >
                  {approval.entity_title}
                </Link>
              </h3>

              <div className="approval-meta">
                <span>Requested by: <strong>{approval.requested_by_name}</strong></span>
                {approval.reviewed_by_name && (
                  <span>Reviewed by: <strong>{approval.reviewed_by_name}</strong></span>
                )}
              </div>

              {approval.comment && (
                <div className="approval-comment">
                  <strong>Comment:</strong> {approval.comment}
                </div>
              )}

              {approval.reviewed_at && (
                <div className="text-muted" style={{ marginTop: '8px' }}>
                  Reviewed: {formatDate(approval.reviewed_at)}
                </div>
              )}

              {/* Only show action buttons for pending items + if user is manager/admin */}
              {approval.status === 'pending' && isManager && (
                <div className="approval-actions">
                  <button
                    className="btn btn-primary btn-sm"
                    onClick={() => openReviewModal(approval.id, 'approve')}
                  >
                    Approve
                  </button>
                  <button
                    className="btn btn-danger btn-sm"
                    onClick={() => openReviewModal(approval.id, 'reject')}
                  >
                    Reject
                  </button>
                </div>
              )}

              {approval.status === 'pending' && !isManager && (
                <div className="text-muted" style={{ marginTop: '12px', fontStyle: 'italic' }}>
                  Only managers and admins can approve or reject requests.
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Review Modal */}
      {reviewingId !== null && (
        <div className="modal-overlay" onClick={closeReviewModal}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>
              {reviewAction === 'approve' ? 'Approve Request' : 'Reject Request'}
            </h2>
            <p style={{ color: '#666' }}>
              {reviewAction === 'approve'
                ? 'Add an optional comment for this approval.'
                : 'Please explain why this request is being rejected (required).'}
            </p>
            <div className="form-group">
              <label>Comment {reviewAction === 'reject' && <span style={{ color: '#dc3545' }}>*</span>}</label>
              <textarea
                value={reviewComment}
                onChange={(e) => setReviewComment(e.target.value)}
                placeholder={
                  reviewAction === 'approve'
                    ? 'Looks good! (optional)'
                    : 'Reason for rejection...'
                }
                rows={4}
                style={{ width: '100%' }}
              />
            </div>
            <div className="form-actions">
              <button
                className={`btn ${reviewAction === 'approve' ? 'btn-primary' : 'btn-danger'}`}
                onClick={handleReview}
                disabled={submitting}
              >
                {submitting
                  ? 'Submitting...'
                  : reviewAction === 'approve'
                    ? 'Confirm Approval'
                    : 'Confirm Rejection'}
              </button>
              <button className="btn btn-secondary" onClick={closeReviewModal}>
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default ApprovalInbox;
