/**
 * CONTRACT TYPES
 *
 * These types mirror the backend's contract schemas.
 *
 * KEY FEATURE: The Contract response includes "vendor_name" and
 * "created_by_name" -- these are convenience fields so the frontend
 * doesn't need to make extra API calls to look up those names.
 *
 * EXAMPLE:
 * Instead of getting {vendor_id: 1} and then calling GET /api/vendors/1
 * to learn the name, we get {vendor_id: 1, vendor_name: "Acme Corp"}
 * all in one response.
 */

// What a contract looks like when we receive it FROM the backend
export interface Contract {
  id: number;
  title: string;
  description: string | null;
  contract_number: string | null;
  vendor_id: number;
  vendor_name: string | null;       // Included so we can display the vendor's name
  created_by_id: number | null;
  created_by_name: string | null;   // Included so we can display who created it
  value: number | null;
  currency: string;            // "USD", "EUR", or "GBP"
  start_date: string | null;
  end_date: string | null;
  status: string;
  document_url: string | null;
  created_at: string;
  updated_at: string;
}

// What we send TO the backend when CREATING a new contract
export interface ContractCreate {
  title: string;
  description?: string;
  contract_number?: string;
  vendor_id: number;                // Required: which vendor is this contract with?
  created_by_id?: number;
  value?: number;
  currency?: string;
  start_date?: string;
  end_date?: string;
  status?: string;
  document_url?: string;
}

// What we send when UPDATING a contract
export interface ContractUpdate {
  title?: string;
  description?: string;
  contract_number?: string;
  vendor_id?: number;
  value?: number;
  currency?: string;
  start_date?: string;
  end_date?: string;
  status?: string;
  document_url?: string;
}
