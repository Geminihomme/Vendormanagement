/**
 * USER TYPES
 *
 * These types mirror the backend's user schemas.
 * They tell TypeScript what shape user data should have.
 *
 * SECURITY NOTE:
 * UserCreate includes a "password" field (for registration),
 * but User (the response type) does NOT include it.
 * The password goes TO the server but never comes back.
 */

// What a user looks like when we receive it FROM the backend
// Notice: NO password field -- the backend never sends it back
export interface User {
  id: number;
  full_name: string;
  email: string;
  role: string;
  is_active: boolean;
  preferred_currency: string;  // "USD", "EUR", or "GBP"
  created_at: string;
  updated_at: string;
}

// What we send TO the backend when CREATING a new user (registration)
export interface UserCreate {
  full_name: string;
  email: string;
  password: string;    // Sent to server, but never returned
  role?: string;
  preferred_currency?: string;
}

// What we send when UPDATING a user's profile
export interface UserUpdate {
  full_name?: string;
  email?: string;
  role?: string;
  is_active?: boolean;
  preferred_currency?: string;
}
