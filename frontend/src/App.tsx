/**
 * APP.TSX - The Root Component
 *
 * WHAT IS A COMPONENT?
 * In React, everything on screen is built from "components" -- reusable
 * building blocks. A button is a component. A form is a component.
 * An entire page is a component. They nest inside each other like
 * Russian dolls.
 *
 * WHAT THIS FILE DOES:
 * App is the TOP-LEVEL component. It defines:
 * 1. The navigation bar (shown on every page)
 * 2. The routing rules (which URL shows which page)
 *
 * WHAT IS ROUTING?
 * When you go to /vendors, React shows the VendorList page.
 * When you go to /vendors/new, React shows the VendorForm page.
 * This is "client-side routing" -- the browser doesn't reload,
 * React just swaps which component is displayed.
 */

import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import VendorList from './pages/VendorList';
import VendorForm from './pages/VendorForm';
import VendorDetail from './pages/VendorDetail';

function App() {
  return (
    <Router>
      <div className="app-container">

        {/* --- NAVIGATION BAR --- */}
        {/* This shows at the top of every page. className="navbar" references
            the .navbar CSS rule in index.css instead of inline styles.
            BEFORE: style={{ display: 'flex', gap: '20px', ... }} (messy)
            AFTER:  className="navbar" (clean -- styles live in CSS file) */}
        <nav className="navbar">
          <Link to="/" className="navbar-brand">
            Vendor Management
          </Link>
          <Link to="/vendors" className="navbar-link">
            All Vendors
          </Link>
          <Link to="/vendors/new" className="navbar-link">
            Add Vendor
          </Link>
        </nav>

        {/* --- PAGE ROUTING --- */}
        {/* React checks the current URL and renders the matching component.
            :id is a "URL parameter" -- React Router extracts it for us. */}
        <Routes>
          <Route path="/" element={<VendorList />} />
          <Route path="/vendors" element={<VendorList />} />
          <Route path="/vendors/new" element={<VendorForm />} />
          <Route path="/vendors/:id" element={<VendorDetail />} />
          <Route path="/vendors/:id/edit" element={<VendorForm />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
