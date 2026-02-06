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

// --- VENDOR API FUNCTIONS ---

export async function getVendors(): Promise<Vendor[]> {
  const response = await api.get<Vendor[]>('/api/vendors/');
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
