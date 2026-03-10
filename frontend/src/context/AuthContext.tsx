/**
 * AUTH CONTEXT (The "Who's Logged In?" Brain)
 * =============================================
 * This file manages login state across the entire app.
 *
 * WHAT IS REACT CONTEXT?
 * Normally, to share data between components, you'd pass it down as "props"
 * from parent to child. But login state needs to be available EVERYWHERE:
 * the navbar (show "Logout"), every page (check if allowed), etc.
 *
 * Context is like a building-wide PA system. Instead of passing a note
 * from room to room, you announce it once and everyone hears it.
 *
 * HOW THIS WORKS:
 * 1. AuthProvider wraps the entire app (in App.tsx)
 * 2. Any component can call useAuth() to get:
 *    - user: the logged-in user (or null)
 *    - login(): log in with email/password
 *    - register(): create account and log in
 *    - logout(): log out
 *    - isLoading: true while checking if stored token is still valid
 *
 * WHERE IS THE TOKEN STORED?
 * In localStorage — the browser's built-in storage that persists
 * even after closing the tab. This is why you stay logged in.
 */

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { User } from '../types/user';
import {
  loginUser,
  registerUser,
  getCurrentUser,
  LoginData,
  RegisterData,
} from '../services/api';

// The shape of the context — what useAuth() returns
interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  login: (data: LoginData) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => void;
}

// Create the context (the PA system)
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// The Provider component that wraps the app
export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true); // true = checking stored token

  // On app load, check if there's a stored token and if it's still valid
  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('auth_token');
      if (!token) {
        setIsLoading(false);
        return;
      }

      try {
        // Send the stored token to /api/auth/me to verify it
        const currentUser = await getCurrentUser();
        setUser(currentUser);
      } catch {
        // Token is invalid or expired — clear it
        localStorage.removeItem('auth_token');
      } finally {
        setIsLoading(false);
      }
    };

    checkAuth();
  }, []);

  const login = useCallback(async (data: LoginData) => {
    const response = await loginUser(data);
    // Store the token so it persists across page reloads
    localStorage.setItem('auth_token', response.access_token);
    setUser(response.user);
  }, []);

  const register = useCallback(async (data: RegisterData) => {
    const response = await registerUser(data);
    localStorage.setItem('auth_token', response.access_token);
    setUser(response.user);
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem('auth_token');
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, isLoading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

// Custom hook — the easy way for any component to access auth state
export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
