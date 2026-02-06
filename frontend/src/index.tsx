/**
 * INDEX.TSX - The very first JavaScript that runs
 *
 * WHAT IT DOES:
 * This file is the "ignition key" for our React application.
 * It takes our App component and injects it into the HTML page.
 *
 * WHY WE NEED IT:
 * React needs to know WHERE to render (the "root" div in index.html)
 * and WHAT to render (our App component). This file connects the two.
 *
 * You rarely need to edit this file.
 */

import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

// Find the <div id="root"> in index.html and render our App inside it
const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);

root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
