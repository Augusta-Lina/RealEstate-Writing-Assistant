/**
 * Main Entry Point
 * =================
 * 
 * This is where React "mounts" your app to the HTML page.
 * It takes your App component and renders it inside the 
 * element with id="root" in index.html
 */

import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'

// StrictMode is a development tool that helps find potential problems
// It doesn't render any visible UI and doesn't affect the production build
ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
