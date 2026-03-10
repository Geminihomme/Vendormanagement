/**
 * API SERVICE
 *
 * WHAT THIS FILE DOES:
 * This is the frontend's "phone" to call the backend.
 * It contains functions that send HTTP requests to our FastAPI backend
 * and return the responses.
 *
 * WHY WE NEED IT:
 * Instead of scattering fetch/axios calls throughout our components,
 * we put them all in one place. This means:
 * - If the backend URL changes, we update ONE file
 * - All components use the same consistent functions
 * - Error handling is centralized
 *
 * HOW IT WORKS:
 * Each function maps to one backend API endpoint:
 *   getVendors()       -> GET    /api/vendors/
 *   getVendor(id)      -> GET    /api/vendors/{id}
 *   createVendor(data) -> POST   /api/vendors/
 *   updateVendor(...)  -> PUT    /api/vendors/{id}
 *   deleteVendor(id)   -> DELETE /api/vendors/{id}
 */

import axios from 'axios';
import { Vendor, VendorCreate, VendorUpdate } from '../types/vendor';
import { User, UserCreate, UserUpdate } from '../types/user';
import { Contract, ContractCreate, ContractUpdate } from '../types/contract';
import { UpcomingRenewal, Notification, CheckNowResponse } from '../types/notification';
import { Payment, PaymentCreate, VendorSpendSummary, MonthlySpend, SpendSummary } from '../types/payment';
import { Approval, ApprovalAction, ApprovalSummary } from '../types/approval';
import { RiskDashboardItem, RiskSummary, RiskAlert, RiskScoreResponse } from '../types/risk';

// The base URL of our backend API.
// In development, the backend runs on port 8000.
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Create a reusable axios instance with default settings.
// This saves us from repeating the base URL in every request.
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// --- AUTH INTERCEPTOR ---
// This automatically attaches the JWT token to every request.
// Think of it as automatically showing your wristband at every door.
// Without this, every API call would need to manually add the token.
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// --- AUTH API FUNCTIONS ---

export interface LoginData {
  email: string;
  password: string;
}

export interface RegisterData {
  full_name: string;
  email: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export async function loginUser(data: LoginData): Promise<AuthResponse> {
  const response = await api.post<AuthResponse>('/api/auth/login', data);
  return response.data;
}

export async function registerUser(data: RegisterData): Promise<AuthResponse> {
  const response = await api.post<AuthResponse>('/api/auth/register', data);
  return response.data;
}

export async function getCurrentUser(): Promise<User> {
  const response = await api.get<User>('/api/auth/me');
  return response.data;
}

// --- VENDOR API FUNCTIONS ---

// Search/filter/sort parameters for vendor listing
export interface VendorSearchParams {
  search?: string;
  status?: string;
  category?: string;
  sort_by?: string;
  sort_order?: string;
}

export async function getVendors(params?: VendorSearchParams): Promise<Vendor[]> {
  const response = await api.get<Vendor[]>('/api/vendors/', { params });
  return response.data;
}

export async function getVendorCategories(): Promise<string[]> {
  const response = await api.get<string[]>('/api/vendors/categories');
  return response.data;
}

export async function getVendor(id: number): Promise<Vendor> {
  const response = await api.get<Vendor>(`/api/vendors/${id}`);
  return response.data;
}

export async function createVendor(vendor: VendorCreate): Promise<Vendor> {
  const response = await api.post<Vendor>('/api/vendors/', vendor);
  return response.data;
}

export async function updateVendor(id: number, vendor: VendorUpdate): Promise<Vendor> {
  const response = await api.put<Vendor>(`/api/vendors/${id}`, vendor);
  return response.data;
}

export async function deleteVendor(id: number): Promise<void> {
  await api.delete(`/api/vendors/${id}`);
}

// --- USER API FUNCTIONS ---

export async function getUsers(): Promise<User[]> {
  const response = await api.get<User[]>('/api/users/');
  return response.data;
}

export async function getUser(id: number): Promise<User> {
  const response = await api.get<User>(`/api/users/${id}`);
  return response.data;
}

export async function createUser(user: UserCreate): Promise<User> {
  const response = await api.post<User>('/api/users/', user);
  return response.data;
}

export async function updateUser(id: number, user: UserUpdate): Promise<User> {
  const response = await api.put<User>(`/api/users/${id}`, user);
  return response.data;
}

export async function deleteUser(id: number): Promise<void> {
  await api.delete(`/api/users/${id}`);
}

// --- CONTRACT API FUNCTIONS ---

export async function getContracts(): Promise<Contract[]> {
  const response = await api.get<Contract[]>('/api/contracts/');
  return response.data;
}

export async function getContract(id: number): Promise<Contract> {
  const response = await api.get<Contract>(`/api/contracts/${id}`);
  return response.data;
}

export async function createContract(contract: ContractCreate): Promise<Contract> {
  const response = await api.post<Contract>('/api/contracts/', contract);
  return response.data;
}

export async function updateContract(id: number, contract: ContractUpdate): Promise<Contract> {
  const response = await api.put<Contract>(`/api/contracts/${id}`, contract);
  return response.data;
}

export async function deleteContract(id: number): Promise<void> {
  await api.delete(`/api/contracts/${id}`);
}

export async function getVendorContracts(vendorId: number): Promise<Contract[]> {
  const response = await api.get<Contract[]>(`/api/contracts/vendor/${vendorId}`);
  return response.data;
}

/**
 * Upload a document (PDF) to an existing contract.
 * Uses FormData (multipart/form-data) instead of JSON.
 */
export async function uploadContractDocument(contractId: number, file: File): Promise<Contract> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await api.post<Contract>(
    `/api/contracts/${contractId}/upload-document`,
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }
  );
  return response.data;
}

// --- NOTIFICATION & RENEWAL API FUNCTIONS ---

export async function getUpcomingRenewals(): Promise<UpcomingRenewal[]> {
  const response = await api.get<UpcomingRenewal[]>('/api/notifications/upcoming-renewals');
  return response.data;
}

export async function getNotifications(unreadOnly: boolean = false): Promise<Notification[]> {
  const response = await api.get<Notification[]>('/api/notifications/', {
    params: { unread_only: unreadOnly },
  });
  return response.data;
}

export async function getUnreadCount(): Promise<number> {
  const response = await api.get<{ unread_count: number }>('/api/notifications/unread-count');
  return response.data.unread_count;
}

export async function markNotificationsRead(notificationIds: number[]): Promise<void> {
  await api.post('/api/notifications/mark-read', { notification_ids: notificationIds });
}

export async function triggerExpiryCheck(): Promise<CheckNowResponse> {
  const response = await api.post<CheckNowResponse>('/api/notifications/check-now');
  return response.data;
}

// --- PAYMENT & ANALYTICS API FUNCTIONS ---

export async function getPayments(): Promise<Payment[]> {
  const response = await api.get<Payment[]>('/api/payments/');
  return response.data;
}

export async function createPayment(payment: PaymentCreate): Promise<Payment> {
  const response = await api.post<Payment>('/api/payments/', payment);
  return response.data;
}

export async function deletePayment(id: number): Promise<void> {
  await api.delete(`/api/payments/${id}`);
}

export async function getVendorPayments(vendorId: number): Promise<Payment[]> {
  const response = await api.get<Payment[]>(`/api/payments/vendor/${vendorId}`);
  return response.data;
}

export async function getSpendSummary(currency?: string): Promise<SpendSummary> {
  const response = await api.get<SpendSummary>('/api/payments/analytics/summary', {
    params: currency ? { currency } : {},
  });
  return response.data;
}

export async function getSpendByVendor(currency?: string): Promise<VendorSpendSummary[]> {
  const response = await api.get<VendorSpendSummary[]>('/api/payments/analytics/by-vendor', {
    params: currency ? { currency } : {},
  });
  return response.data;
}

export async function getMonthlySpend(year?: number, currency?: string): Promise<MonthlySpend[]> {
  const params: Record<string, any> = {};
  if (year) params.year = year;
  if (currency) params.currency = currency;
  const response = await api.get<MonthlySpend[]>('/api/payments/analytics/monthly', { params });
  return response.data;
}

// --- APPROVAL API FUNCTIONS ---

export async function getApprovalSummary(): Promise<ApprovalSummary> {
  const response = await api.get<ApprovalSummary>('/api/approvals/summary');
  return response.data;
}

export async function getPendingApprovals(): Promise<Approval[]> {
  const response = await api.get<Approval[]>('/api/approvals/pending');
  return response.data;
}

export async function getAllApprovals(params?: {
  status?: string;
  approval_type?: string;
}): Promise<Approval[]> {
  const response = await api.get<Approval[]>('/api/approvals/', { params });
  return response.data;
}

export async function getApproval(id: number): Promise<Approval> {
  const response = await api.get<Approval>(`/api/approvals/${id}`);
  return response.data;
}

export async function reviewApproval(id: number, action: ApprovalAction): Promise<Approval> {
  const response = await api.post<Approval>(`/api/approvals/${id}/review`, action);
  return response.data;
}

// --- RISK ASSESSMENT API FUNCTIONS ---

export async function getRiskSummary(): Promise<RiskSummary> {
  const response = await api.get<RiskSummary>('/api/risk/summary');
  return response.data;
}

export async function getRiskDashboard(): Promise<RiskDashboardItem[]> {
  const response = await api.get<RiskDashboardItem[]>('/api/risk/dashboard');
  return response.data;
}

export async function getRiskAlerts(): Promise<RiskAlert[]> {
  const response = await api.get<RiskAlert[]>('/api/risk/alerts');
  return response.data;
}

export async function getVendorRisk(vendorId: number): Promise<RiskScoreResponse> {
  const response = await api.get<RiskScoreResponse>(`/api/risk/vendor/${vendorId}`);
  return response.data;
}

export async function recalculateAllRisks(): Promise<{ vendors_assessed: number }> {
  const response = await api.post<{ vendors_assessed: number }>('/api/risk/recalculate');
  return response.data;
}

export async function recalculateVendorRisk(vendorId: number): Promise<RiskScoreResponse> {
  const response = await api.post<RiskScoreResponse>(`/api/risk/vendor/${vendorId}/recalculate`);
  return response.data;
}

// --- REPORT DOWNLOAD FUNCTIONS ---
// These use a special "blob" download pattern.
// Normal API calls return JSON (text data). Report downloads return FILES
// (binary data like Excel spreadsheets). "Blob" means "Binary Large Object" —
// it's how browsers handle raw file data.
//
// The pattern works like this:
// 1. Request the file from the backend (responseType: 'blob' tells axios to expect binary)
// 2. Create a temporary URL pointing to the downloaded data
// 3. Create a hidden <a> link, set its href to that URL, and "click" it
// 4. The browser's download dialog appears with the file
// 5. Clean up the temporary URL

/**
 * Helper: triggers a browser download from an API response.
 * Think of it as creating an invisible "Download" button and clicking it.
 */
function triggerDownload(data: Blob, filename: string) {
  const url = window.URL.createObjectURL(data);
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', filename);
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}

// CSV Downloads — lightweight text files, open in any spreadsheet app
export async function downloadVendorsCSV(): Promise<void> {
  const response = await api.get('/api/reports/vendors/csv', { responseType: 'blob' });
  triggerDownload(response.data, 'vendors.csv');
}

export async function downloadContractsCSV(): Promise<void> {
  const response = await api.get('/api/reports/contracts/csv', { responseType: 'blob' });
  triggerDownload(response.data, 'contracts.csv');
}

export async function downloadPaymentsCSV(): Promise<void> {
  const response = await api.get('/api/reports/payments/csv', { responseType: 'blob' });
  triggerDownload(response.data, 'payments.csv');
}

// Excel Downloads — rich formatted reports with multiple sheets, charts-ready
export async function downloadSpendReportExcel(): Promise<void> {
  const response = await api.get('/api/reports/spend/excel', { responseType: 'blob' });
  triggerDownload(response.data, 'spend_report.xlsx');
}

export async function downloadExpiryReportExcel(): Promise<void> {
  const response = await api.get('/api/reports/expiry/excel', { responseType: 'blob' });
  triggerDownload(response.data, 'contract_expiry_report.xlsx');
}

export async function downloadRiskReportExcel(): Promise<void> {
  const response = await api.get('/api/reports/risk/excel', { responseType: 'blob' });
  triggerDownload(response.data, 'risk_report.xlsx');
}

// --- CURRENCY API FUNCTIONS ---
// These manage exchange rates and user currency preferences.
// Think of it as the controls on an international shopping site:
// "Show prices in EUR" / "View exchange rates"

export interface ExchangeRate {
  currency_code: string;
  rate_to_usd: number;
  updated_at: string | null;
}

export interface SupportedCurrency {
  code: string;
  name: string;
  symbol: string;
}

export async function getExchangeRates(): Promise<ExchangeRate[]> {
  const response = await api.get<ExchangeRate[]>('/api/currency/rates');
  return response.data;
}

export async function getSupportedCurrencies(): Promise<SupportedCurrency[]> {
  const response = await api.get<SupportedCurrency[]>('/api/currency/supported');
  return response.data;
}

export async function updateCurrencyPreference(preferred_currency: string): Promise<void> {
  await api.put('/api/currency/preference', { preferred_currency });
}
