/**
 * LOGIN PAGE
 * ===========
 * The "front door" of the application.
 * Users enter their email and password to get their JWT "wristband."
 *
 * HOW IT CONNECTS:
 * 1. User fills in email + password
 * 2. On submit, calls useAuth().login() from AuthContext
 * 3. AuthContext calls POST /api/auth/login on the backend
 * 4. Backend verifies password, returns a JWT token
 * 5. AuthContext stores the token in localStorage
 * 6. User is redirected to the home page
 *
 * If the credentials are wrong, the backend returns a 401 error,
 * and we show "Invalid email or password" (same message for both
 * wrong email and wrong password — prevents information leakage).
 */

import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';

function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsSubmitting(true);

    try {
      await login({ email, password });
      navigate('/');  // Redirect to home after login
    } catch (err) {
      if (axios.isAxiosError(err) && err.response) {
        setError(err.response.data.detail || 'Login failed');
      } else {
        setError('Unable to connect to server');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        <h1 className="auth-title">Welcome Back</h1>
        <p className="auth-subtitle">Sign in to your vendor management account</p>

        {error && <div className="alert alert-error">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@company.com"
              required
            />
          </div>

          <div className="form-group">
            <label>Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Your password"
              required
            />
          </div>

          <button
            type="submit"
            className="btn btn-primary btn-lg auth-submit"
            disabled={isSubmitting}
          >
            {isSubmitting ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        <p className="auth-switch">
          Don't have an account?{' '}
          <Link to="/register" className="text-link">Create one</Link>
        </p>
      </div>
    </div>
  );
}

export default LoginPage;
