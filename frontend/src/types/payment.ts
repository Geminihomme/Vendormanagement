/**
 * PAYMENT & ANALYTICS TYPES
 *
 * These types define the shape of data for payments and spend analytics.
 *
 * PAYMENT: A single payment record (like one line in a checkbook)
 * VENDOR SPEND SUMMARY: Totals per vendor (like an Excel pivot table)
 * MONTHLY SPEND: Totals per month (like a monthly bank statement)
 * SPEND SUMMARY: The grand total across everything
 */

// What a payment looks like when returned from the API
export interface Payment {
  id: number;
  vendor_id: number;
  vendor_name: string | null;
  contract_id: number | null;
  contract_title: string | null;
  amount: number;
  payment_date: string;
  invoice_number: string | null;
  description: string | null;
  status: string;
  payment_method: string | null;
  created_at: string;
  updated_at: string;
}

// What we send when creating a new payment
export interface PaymentCreate {
  vendor_id: number;
  contract_id?: number;
  amount: number;
  payment_date: string;
  invoice_number?: string;
  description?: string;
  status?: string;
  payment_method?: string;
}

// Analytics: total spend per vendor
export interface VendorSpendSummary {
  vendor_id: number;
  vendor_name: string;
  total_spent: number;
  payment_count: number;
  average_payment: number;
  last_payment_date: string | null;
}

// Analytics: spending per month
export interface MonthlySpend {
  year: number;
  month: number;
  month_name: string;
  total_spent: number;
  payment_count: number;
}

// Analytics: overall summary
export interface SpendSummary {
  total_spent: number;
  payment_count: number;
  average_payment: number;
  vendor_count: number;
}
