/**
 * RISK ASSESSMENT TYPES
 *
 * These types define the shape of risk scoring data.
 * A risk score is like a credit score for a vendor — 0-100,
 * where lower is better (less risky).
 */

// One factor in the risk breakdown (like one section of a credit report)
export interface RiskFactorDetail {
  name: string;         // "Contract Value"
  score: number;        // 16.0
  max_score: number;    // 25.0
  description: string;  // "Total contract value is $150,000"
}

// Full risk report for one vendor
export interface RiskScoreResponse {
  vendor_id: number;
  vendor_name: string;
  overall_score: number;        // 0-100
  risk_level: 'low' | 'medium' | 'high' | 'critical';
  factors: RiskFactorDetail[];
  calculated_at: string | null;
}

// One row in the dashboard table
export interface RiskDashboardItem {
  vendor_id: number;
  vendor_name: string;
  category: string | null;
  status: string;
  overall_score: number;
  risk_level: string;
  contract_count: number;
  total_contract_value: number;
  overdue_payments: number;
  expiring_soon: number;
}

// Dashboard header stats
export interface RiskSummary {
  low: number;
  medium: number;
  high: number;
  critical: number;
  total: number;
  average_score: number;
}

// A triggered risk alert
export interface RiskAlert {
  vendor_id: number;
  vendor_name: string;
  risk_level: string;
  overall_score: number;
  alert_reason: string;
  triggered_at: string;
}
