/**
 * APPROVAL TYPES
 *
 * These types define the shape of approval data flowing between
 * the frontend and backend.
 *
 * An approval is a REQUEST to add a vendor or finalize a contract.
 * It sits in a manager's inbox until someone reviews it.
 */

// A full approval record from the backend
export interface Approval {
  id: number;
  approval_type: 'vendor' | 'contract';  // What kind of thing needs approval
  entity_id: number;                      // The vendor or contract ID
  entity_title: string;                   // "Acme Corp" or "Acme IT Contract"
  status: 'pending' | 'approved' | 'rejected';
  requested_by_id: number;
  requested_by_name: string;              // "Lisa Park"
  reviewed_by_id: number | null;
  reviewed_by_name: string;               // "Mike Johnson" (empty if pending)
  comment: string | null;
  created_at: string;
  reviewed_at: string | null;
}

// What the manager sends when approving/rejecting
export interface ApprovalAction {
  action: 'approve' | 'reject';
  comment?: string;
}

// Dashboard badge counts
export interface ApprovalSummary {
  pending: number;
  approved: number;
  rejected: number;
  total: number;
}
