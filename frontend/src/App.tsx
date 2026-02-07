/**
 * APP.TSX - The Root Component
 *
 * WHAT THIS FILE DOES:
 * App is the TOP-LEVEL component. It defines:
 * 1. The AuthProvider (makes login state available everywhere)
 * 2. The navigation bar (shown on every page)
 * 3. The routing rules (which URL shows which page)
 * 4. Protected routes (only logged-in users can access data pages)
 *
 * THE AUTH FLOW:
 * - AuthProvider wraps everything — like a security fence around the building
 * - Login and Register pages are OUTSIDE the fence (anyone can access them)
 * - All other pages are INSIDE the fence (ProtectedRoute checks your wristband)
 * - The navbar shows different links depending on whether you're logged in
 */

import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useNavigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import VendorList from './pages/VendorList';
import VendorForm from './pages/VendorForm';
import VendorDetail from './pages/VendorDetail';
import ContractForm from './pages/ContractForm';
import RenewalsDashboard from './pages/RenewalsDashboard';
import SpendAnalytics from './pages/SpendAnalytics';
import PaymentForm from './pages/PaymentForm';
import SearchPage from './pages/SearchPage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';

/**
 * NAVBAR COMPONENT
 * Separated from App so it can use useAuth() (needs to be inside AuthProvider).
 * Shows navigation links when logged in, or Login/Register when logged out.
 */
function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <nav className="navbar">
      <Link to="/" className="navbar-brand">
        Vendor Management
      </Link>

      {user ? (
        <>
          {/* Logged in — show app navigation */}
          <Link to="/vendors" className="navbar-link">All Vendors</Link>
          <Link to="/vendors/new" className="navbar-link">Add Vendor</Link>
          <Link to="/renewals" className="navbar-link">Renewals</Link>
          <Link to="/analytics" className="navbar-link">Analytics</Link>
          <Link to="/search" className="navbar-link">Search</Link>

          <div className="navbar-user">
            <span className="navbar-username">{user.full_name}</span>
            <button onClick={handleLogout} className="btn btn-sm btn-secondary">
              Logout
            </button>
          </div>
        </>
      ) : (
        <>
          {/* Not logged in — show auth links */}
          <div className="navbar-user">
            <Link to="/login" className="btn btn-sm btn-primary">Sign In</Link>
            <Link to="/register" className="navbar-link">Create Account</Link>
          </div>
        </>
      )}
    </nav>
  );
}

function App() {
  return (
    <Router>
      <AuthProvider>
        <div className="app-container">
          <Navbar />

          <Routes>
            {/* Public routes — anyone can access */}
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />

            {/* Protected routes — must be logged in */}
            <Route path="/" element={<ProtectedRoute><VendorList /></ProtectedRoute>} />
            <Route path="/vendors" element={<ProtectedRoute><VendorList /></ProtectedRoute>} />
            <Route path="/vendors/new" element={<ProtectedRoute><VendorForm /></ProtectedRoute>} />
            <Route path="/vendors/:id" element={<ProtectedRoute><VendorDetail /></ProtectedRoute>} />
            <Route path="/vendors/:id/edit" element={<ProtectedRoute><VendorForm /></ProtectedRoute>} />
            <Route path="/vendors/:vendorId/contracts/new" element={<ProtectedRoute><ContractForm /></ProtectedRoute>} />
            <Route path="/renewals" element={<ProtectedRoute><RenewalsDashboard /></ProtectedRoute>} />
            <Route path="/analytics" element={<ProtectedRoute><SpendAnalytics /></ProtectedRoute>} />
            <Route path="/payments/new" element={<ProtectedRoute><PaymentForm /></ProtectedRoute>} />
            <Route path="/search" element={<ProtectedRoute><SearchPage /></ProtectedRoute>} />
          </Routes>
        </div>
      </AuthProvider>
    </Router>
  );
}

export default App;
