/**
 * VENDOR TYPES
 *
 * WHAT ARE TYPES?
 * Types are like labels that describe the shape of data.
 * They tell TypeScript: "A Vendor object must have a name (text),
 * an id (number), etc." If you accidentally try to use a number
 * where text is expected, TypeScript warns you BEFORE the code runs.
 *
 * WHY WE NEED THEM:
 * Without types, you could accidentally write: vendor.nme (typo)
 * instead of vendor.name, and you wouldn't know until users see a bug.
 * Types catch this instantly in your editor.
 *
 * These types MIRROR the backend schemas (backend/app/schemas/vendor.py)
 * so the frontend and backend agree on what data looks like.
 */

// What a vendor looks like when we receive it FROM the backend
export interface Vendor {
  id: number;
  name: string;
  email: string;
  phone: string | null;
  website: string | null;
  description: string | null;
  category: string | null;
  tax_id: string | null;
  address: string | null;
  city: string | null;
  state: string | null;
  zip_code: string | null;
  country: string | null;
  status: string;
  created_at: string;
  updated_at: string;
}

// What we send TO the backend when CREATING a new vendor
// (no id, no timestamps -- the backend generates those)
export interface VendorCreate {
  name: string;
  email: string;
  phone?: string;
  website?: string;
  description?: string;
  category?: string;
  tax_id?: string;
  address?: string;
  city?: string;
  state?: string;
  zip_code?: string;
  country?: string;
}

// What we send TO the backend when UPDATING a vendor
// (everything optional -- only send what changed)
export interface VendorUpdate {
  name?: string;
  email?: string;
  phone?: string;
  website?: string;
  description?: string;
  category?: string;
  tax_id?: string;
  address?: string;
  city?: string;
  state?: string;
  zip_code?: string;
  country?: string;
  status?: string;
}
