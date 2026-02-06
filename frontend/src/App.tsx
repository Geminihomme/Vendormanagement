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
      <div style={{ fontFamily: 'Arial, sans-serif', maxWidth: '1200px', margin: '0 auto', padding: '20px' }}>

        {/* --- NAVIGATION BAR --- */}
        {/* This shows at the top of every page */}
        <nav style={{
          display: 'flex',
          gap: '20px',
          padding: '15px 0',
          borderBottom: '2px solid #e0e0e0',
          marginBottom: '30px',
          alignItems: 'center',
        }}>
          <Link to="/" style={{ fontSize: '20px', fontWeight: 'bold', textDecoration: 'none', color: '#333' }}>
            Vendor Management
          </Link>
          <Link to="/vendors" style={{ textDecoration: 'none', color: '#0066cc' }}>
            All Vendors
          </Link>
          <Link to="/vendors/new" style={{ textDecoration: 'none', color: '#0066cc' }}>
            Add Vendor
          </Link>
        </nav>

        {/* --- PAGE ROUTING --- */}
        {/* React checks the URL and shows the matching component */}
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
