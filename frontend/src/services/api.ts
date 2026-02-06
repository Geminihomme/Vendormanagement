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
 *
 * THIS IS DIFFERENT from other API calls:
 * - Normal calls send JSON: {"title": "My Contract"}
 * - File uploads send FormData (multipart/form-data)
 *
 * FormData is a browser API that packages files + text together.
 * It's like putting a letter AND a photo into the same envelope.
 *
 * The 'Content-Type' header is NOT set manually -- the browser
 * automatically adds it with the correct "boundary" string that
 * separates the different parts of the form data.
 */
export async function uploadContractDocument(contractId: number, file: File): Promise<Contract> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await api.post<Contract>(
    `/api/contracts/${contractId}/upload-document`,
    formData,
    {
      headers: {
        // Override the default JSON content type.
        // Setting to undefined lets the browser auto-detect the right type.
        'Content-Type': 'multipart/form-data',
      },
    }
  );
  return response.data;
}
