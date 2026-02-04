/**
 * AI Writing Assistant - React Frontend
 * ======================================
 * 
 * This is a simple React app that connects to our FastAPI backend.
 * It demonstrates both regular and streaming API calls.
 * 
 * KEY CONCEPTS FOR LEARNERS:
 * - useState: React hook to store and update data
 * - async/await: Modern way to handle asynchronous operations
 * - fetch: Browser API for making HTTP requests
 * - EventSource-like streaming: Reading data as it arrives
 */

import { useState } from 'react'
import './App.css'

// ============================================================================
// CONFIGURATION
// ============================================================================

// API URL - Change this to your deployed backend URL
// In development: http://localhost:8000
// In production: Your Railway/Render URL
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// ============================================================================
// MAIN APP COMPONENT
// ============================================================================

function App() {
  // --------------------------------------------------------------------------
  // STATE - These variables store our app's data
  // --------------------------------------------------------------------------
  
  // The user's writing prompt
  const [prompt, setPrompt] = useState('')
  
  // Type of writing (blog post, email, etc.)
  const [writingType, setWritingType] = useState('blog_post')
  
  // Tone of writing (professional, casual, etc.)
  const [tone, setTone] = useState('professional')
  
  // The generated content from the AI
  const [content, setContent] = useState('')
  
  // Loading state - true while waiting for response
  const [isLoading, setIsLoading] = useState(false)
  
  // Error message if something goes wrong
  const [error, setError] = useState('')
  
  // Whether to use streaming or not
  const [useStreaming, setUseStreaming] = useState(true)

  // --------------------------------------------------------------------------
  // REGULAR (NON-STREAMING) GENERATION
  // --------------------------------------------------------------------------
  
  const generateRegular = async () => {
    /**
     * This function calls the /generate endpoint.
     * It waits for the COMPLETE response before showing anything.
     * 
     * Flow:
     * 1. Send POST request with our data
     * 2. Wait for complete response
     * 3. Display the result
     */
    
    try {
      const response = await fetch(`${API_URL}/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          prompt: prompt,
          writing_type: writingType,
          tone: tone,
        }),
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      setContent(data.content)
      
    } catch (err) {
      setError(`Error: ${err.message}`)
    }
  }

  // --------------------------------------------------------------------------
  // STREAMING GENERATION
  // --------------------------------------------------------------------------
  
  const generateStreaming = async () => {
    /**
     * This function calls the /generate/stream endpoint.
     * It reads and displays data as it arrives, word by word!
     * 
     * Flow:
     * 1. Send POST request
     * 2. Get a "reader" for the response stream
     * 3. Read chunks as they arrive
     * 4. Update the display with each chunk
     * 
     * This is more complex but provides a MUCH better user experience!
     */
    
    try {
      const response = await fetch(`${API_URL}/generate/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          prompt: prompt,
          writing_type: writingType,
          tone: tone,
        }),
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      // Get a reader for the response body stream
      const reader = response.body.getReader()
      
      // TextDecoder converts raw bytes to text
      const decoder = new TextDecoder()
      
      // Clear previous content before streaming new content
      setContent('')

      // Read the stream in a loop
      while (true) {
        // Read the next chunk
        const { done, value } = await reader.read()
        
        // If done is true, we've reached the end
        if (done) break
        
        // Decode the chunk from bytes to text
        const chunk = decoder.decode(value)
        
        // The data comes in SSE format: "data: text\n\n"
        // We need to extract just the text part
        const lines = chunk.split('\n')
        
        for (const line of lines) {
          // Skip empty lines
          if (!line.startsWith('data: ')) continue
          
          // Extract the data after "data: "
          const data = line.slice(6)
          
          // Check for end signal or errors
          if (data === '[DONE]') continue
          if (data.startsWith('[ERROR]')) {
            throw new Error(data)
          }
          
          // Append the new text to our content
          // Using the callback form of setState to ensure we get the latest value
          setContent(prev => prev + data)
        }
      }
      
    } catch (err) {
      setError(`Error: ${err.message}`)
    }
  }

  // --------------------------------------------------------------------------
  // FORM SUBMISSION HANDLER
  // --------------------------------------------------------------------------
  
  const handleSubmit = async (e) => {
    // Prevent the default form submission (which would reload the page)
    e.preventDefault()
    
    // Reset state
    setError('')
    setContent('')
    setIsLoading(true)
    
    // Choose which generation method to use
    if (useStreaming) {
      await generateStreaming()
    } else {
      await generateRegular()
    }
    
    setIsLoading(false)
  }

  // --------------------------------------------------------------------------
  // RENDER THE UI
  // --------------------------------------------------------------------------
  
  return (
    <div className="app">
      <header className="header">
        <h1>✍️ AI Writing Assistant</h1>
        <p>Powered by Claude AI</p>
      </header>

      <main className="main">
        {/* INPUT FORM */}
        <form onSubmit={handleSubmit} className="form">
          
          {/* Writing Prompt */}
          <div className="form-group">
            <label htmlFor="prompt">What would you like me to write?</label>
            <textarea
              id="prompt"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="E.g., Write a blog post about the benefits of learning to code..."
              rows={4}
              required
            />
          </div>

          {/* Writing Type Selector */}
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="type">Writing Type</label>
              <select
                id="type"
                value={writingType}
                onChange={(e) => setWritingType(e.target.value)}
              >
                <option value="blog_post">Blog Post</option>
                <option value="email">Email</option>
                <option value="social_media">Social Media</option>
                <option value="essay">Essay</option>
                <option value="story">Story</option>
                <option value="code_documentation">Code Documentation</option>
              </select>
            </div>

            {/* Tone Selector */}
            <div className="form-group">
              <label htmlFor="tone">Tone</label>
              <select
                id="tone"
                value={tone}
                onChange={(e) => setTone(e.target.value)}
              >
                <option value="professional">Professional</option>
                <option value="casual">Casual</option>
                <option value="friendly">Friendly</option>
                <option value="formal">Formal</option>
                <option value="humorous">Humorous</option>
              </select>
            </div>
          </div>

          {/* Streaming Toggle */}
          <div className="form-group checkbox-group">
            <label>
              <input
                type="checkbox"
                checked={useStreaming}
                onChange={(e) => setUseStreaming(e.target.checked)}
              />
              Enable streaming (see text appear word-by-word)
            </label>
          </div>

          {/* Submit Button */}
          <button 
            type="submit" 
            disabled={isLoading || !prompt.trim()}
            className="submit-btn"
          >
            {isLoading ? '✨ Generating...' : '🚀 Generate Content'}
          </button>
        </form>

        {/* ERROR DISPLAY */}
        {error && (
          <div className="error">
            ⚠️ {error}
          </div>
        )}

        {/* OUTPUT DISPLAY */}
        {content && (
          <div className="output">
            <h2>Generated Content:</h2>
            <div className="content">
              {content}
            </div>
          </div>
        )}
      </main>

      <footer className="footer">
        <p>
          Built with FastAPI + React | 
          <a href={`${API_URL}/docs`} target="_blank" rel="noopener noreferrer">
            API Docs
          </a>
        </p>
      </footer>
    </div>
  )
}

export default App
