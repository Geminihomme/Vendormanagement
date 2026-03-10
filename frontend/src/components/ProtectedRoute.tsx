/**
 * PROTECTED ROUTE (The Velvet Rope)
 * ===================================
 * This component wraps pages that require login.
 *
 * HOW IT WORKS:
 * Instead of showing the page directly, we check:
 * - Is the auth system still loading (checking stored token)? -> Show "Loading..."
 * - Is the user logged in? -> Show the page
 * - Is the user NOT logged in? -> Redirect to /login
 *
 * USAGE (in App.tsx):
 *   <Route path="/vendors" element={
 *     <ProtectedRoute><VendorList /></ProtectedRoute>
 *   } />
 *
 * Think of it like a bouncer at a VIP section. The page content is
 * inside the VIP area. If you have a wristband (JWT token), you get
 * through. If not, you're sent to the entrance (login page).
 */

import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { user, isLoading } = useAuth();

  // Still checking if the stored token is valid — show loading
  if (isLoading) {
    return <div className="loading">Checking authentication...</div>;
  }

  // Not logged in — redirect to login page
  if (!user) {
    return <Navigate to="/login" replace />;
  }

  // Logged in — show the actual page
  return <>{children}</>;
}

export default ProtectedRoute;
