import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import './App.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const PROPERTY_TYPES = [
  { value: 'house', label: 'House' },
  { value: 'condo', label: 'Condo/Apartment' },
  { value: 'townhouse', label: 'Townhouse' },
  { value: 'land', label: 'Land/Lot' },
]

const FEATURES = [
  'Updated kitchen', 'Hardwood floors', 'Open floor plan', 'Natural light', 'Fireplace',
  'High ceilings', 'Walk-in closet', 'Pool', 'Fenced yard', 'Deck/patio',
  'Garage', 'Recently renovated', 'Move-in ready', 'Great view', 'Smart home features',
  'In-unit laundry', 'Pet-friendly', 'Balcony', 'Stainless steel appliances', 'Granite/quartz countertops'
]

function renderMarkdown(text) {
  if (!text) return null
  const parts = text.split(/(\*\*.*?\*\*)/g)
  return parts.map((part, i) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={i}>{part.slice(2, -2)}</strong>
    }
    return part
  })
}

function App() {
  // Form state
  const [propertyType, setPropertyType] = useState('house')
  const [listingPurpose, setListingPurpose] = useState('sale')
  const [bedrooms, setBedrooms] = useState('')
  const [bathrooms, setBathrooms] = useState('')
  const [sqft, setSqft] = useState('')
  const [price, setPrice] = useState('')
  const [address, setAddress] = useState('')
  const [selectedFeatures, setSelectedFeatures] = useState([])
  const [otherFeatures, setOtherFeatures] = useState('')
  const [additionalNotes, setAdditionalNotes] = useState('')
  const [images, setImages] = useState([])

  // Output state
  const [description, setDescription] = useState('')
  const [socialCaption, setSocialCaption] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isRegeneratingDescription, setIsRegeneratingDescription] = useState(false)
  const [isRegeneratingSocial, setIsRegeneratingSocial] = useState(false)
  const [error, setError] = useState('')
  const [copiedDescription, setCopiedDescription] = useState(false)
  const [copiedSocial, setCopiedSocial] = useState(false)

  // Image upload with react-dropzone
  const onDrop = useCallback((acceptedFiles) => {
    const newImages = acceptedFiles.slice(0, 5 - images.length).map(file => ({
      file,
      preview: URL.createObjectURL(file)
    }))
    setImages(prev => [...prev, ...newImages].slice(0, 5))
  }, [images.length])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'image/jpeg': [], 'image/png': [], 'image/webp': [] },
    maxSize: 5 * 1024 * 1024,
    disabled: images.length >= 5
  })

  const removeImage = (index) => {
    setImages(prev => {
      const newImages = [...prev]
      URL.revokeObjectURL(newImages[index].preview)
      newImages.splice(index, 1)
      return newImages
    })
  }

  const toggleFeature = (feature) => {
    setSelectedFeatures(prev =>
      prev.includes(feature)
        ? prev.filter(f => f !== feature)
        : [...prev, feature]
    )
  }

  const buildFormData = () => {
    const formData = new FormData()
    formData.append('property_type', propertyType)
    formData.append('listing_purpose', listingPurpose)
    formData.append('bedrooms', bedrooms)
    formData.append('bathrooms', bathrooms)
    formData.append('sqft', sqft)
    formData.append('price', price)
    formData.append('address', address)
    formData.append('features', JSON.stringify([...selectedFeatures, ...(otherFeatures ? [otherFeatures] : [])]))
    formData.append('additional_notes', additionalNotes)
    images.forEach((img) => {
      formData.append('images', img.file)
    })
    return formData
  }

  const handleGenerate = async (e) => {
    e.preventDefault()
    setError('')
    setIsLoading(true)
    setDescription('')
    setSocialCaption('')

    try {
      const formData = buildFormData()
      const response = await fetch(`${API_URL}/generate-listing`, {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      setDescription(data.description)
      setSocialCaption(data.social_caption)
    } catch (err) {
      setError(err.message)
    } finally {
      setIsLoading(false)
    }
  }

  const handleRegenerateDescription = async () => {
    setIsRegeneratingDescription(true)
    try {
      const formData = buildFormData()
      formData.append('section', 'description')
      const response = await fetch(`${API_URL}/regenerate-section`, {
        method: 'POST',
        body: formData,
      })
      if (!response.ok) throw new Error('Failed to regenerate')
      const data = await response.json()
      setDescription(data.content)
    } catch (err) {
      setError(err.message)
    } finally {
      setIsRegeneratingDescription(false)
    }
  }

  const handleRegenerateSocial = async () => {
    setIsRegeneratingSocial(true)
    try {
      const formData = buildFormData()
      formData.append('section', 'social')
      const response = await fetch(`${API_URL}/regenerate-section`, {
        method: 'POST',
        body: formData,
      })
      if (!response.ok) throw new Error('Failed to regenerate')
      const data = await response.json()
      setSocialCaption(data.content)
    } catch (err) {
      setError(err.message)
    } finally {
      setIsRegeneratingSocial(false)
    }
  }

  const copyToClipboard = async (text, type) => {
    try {
      await navigator.clipboard.writeText(text)
      if (type === 'description') {
        setCopiedDescription(true)
        setTimeout(() => setCopiedDescription(false), 2000)
      } else {
        setCopiedSocial(true)
        setTimeout(() => setCopiedSocial(false), 2000)
      }
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  const hasOutput = description || socialCaption

  return (
    <div className="app">
      <header className="header">
        <h1>Real Estate Listing Assistant</h1>
        <p>Generate professional listing descriptions in seconds</p>
      </header>

      <main className="main-content">
        {/* Left Column - Form */}
        <div className="form-column">
          <form onSubmit={handleGenerate} className="property-form">
            {/* Property Type & Purpose */}
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="propertyType">Property Type</label>
                <select
                  id="propertyType"
                  value={propertyType}
                  onChange={(e) => setPropertyType(e.target.value)}
                >
                  {PROPERTY_TYPES.map(type => (
                    <option key={type.value} value={type.value}>{type.label}</option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label>Listing Purpose</label>
                <div className="toggle-group">
                  <button
                    type="button"
                    className={`toggle-btn ${listingPurpose === 'sale' ? 'active' : ''}`}
                    onClick={() => setListingPurpose('sale')}
                  >
                    For Sale
                  </button>
                  <button
                    type="button"
                    className={`toggle-btn ${listingPurpose === 'rent' ? 'active' : ''}`}
                    onClick={() => setListingPurpose('rent')}
                  >
                    For Rent
                  </button>
                </div>
              </div>
            </div>

            {/* Property Details */}
            <div className="form-row four-col">
              <div className="form-group">
                <label htmlFor="bedrooms">Beds</label>
                <input
                  type="number"
                  id="bedrooms"
                  min="0"
                  max="10"
                  value={bedrooms}
                  onChange={(e) => setBedrooms(e.target.value)}
                  placeholder="0"
                />
              </div>
              <div className="form-group">
                <label htmlFor="bathrooms">Baths</label>
                <input
                  type="number"
                  id="bathrooms"
                  min="0"
                  max="10"
                  step="0.5"
                  value={bathrooms}
                  onChange={(e) => setBathrooms(e.target.value)}
                  placeholder="0"
                />
              </div>
              <div className="form-group">
                <label htmlFor="sqft">Size (sqft)</label>
                <input
                  type="number"
                  id="sqft"
                  min="0"
                  value={sqft}
                  onChange={(e) => setSqft(e.target.value)}
                  placeholder="0"
                />
              </div>
              <div className="form-group">
                <label htmlFor="price">Price</label>
                <input
                  type="number"
                  id="price"
                  min="0"
                  value={price}
                  onChange={(e) => setPrice(e.target.value)}
                  placeholder="$"
                />
              </div>
            </div>

            {/* Address */}
            <div className="form-group">
              <label htmlFor="address">Address or Neighborhood</label>
              <input
                type="text"
                id="address"
                value={address}
                onChange={(e) => setAddress(e.target.value)}
                placeholder="e.g., 123 Main St, Austin TX or 'Downtown Seattle'"
              />
            </div>

            {/* Features */}
            <div className="form-group">
              <label>Standout Features</label>
              <div className="features-grid">
                {FEATURES.map(feature => (
                  <button
                    key={feature}
                    type="button"
                    className={`feature-chip ${selectedFeatures.includes(feature) ? 'active' : ''}`}
                    onClick={() => toggleFeature(feature)}
                  >
                    {feature}
                  </button>
                ))}
              </div>
              <input
                type="text"
                className="other-features"
                value={otherFeatures}
                onChange={(e) => setOtherFeatures(e.target.value)}
                placeholder="Other features..."
              />
            </div>

            {/* Additional Notes */}
            <div className="form-group">
              <label htmlFor="notes">Additional Notes</label>
              <textarea
                id="notes"
                value={additionalNotes}
                onChange={(e) => setAdditionalNotes(e.target.value)}
                placeholder="Any special instructions or details for the AI..."
                rows={3}
              />
            </div>

            {/* Image Upload */}
            <div className="form-group">
              <label>Property Photos (optional)</label>
              <div
                {...getRootProps()}
                className={`dropzone ${isDragActive ? 'active' : ''} ${images.length >= 5 ? 'disabled' : ''}`}
              >
                <input {...getInputProps()} />
                {images.length >= 5 ? (
                  <p>Maximum 5 images reached</p>
                ) : isDragActive ? (
                  <p>Drop images here...</p>
                ) : (
                  <p>Drag & drop images here, or click to browse<br /><span className="dropzone-hint">JPG, PNG, WEBP - Max 5MB each</span></p>
                )}
              </div>
              {images.length > 0 && (
                <div className="image-previews">
                  {images.map((img, index) => (
                    <div key={index} className="image-preview">
                      <img src={img.preview} alt={`Preview ${index + 1}`} />
                      <button
                        type="button"
                        className="remove-image"
                        onClick={() => removeImage(index)}
                      >
                        x
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Generate Button */}
            <button
              type="submit"
              className="generate-btn"
              disabled={isLoading}
            >
              {isLoading ? 'Crafting your listing...' : 'Generate Listing'}
            </button>
          </form>
        </div>

        {/* Right Column - Output */}
        <div className="output-column">
          {error && (
            <div className="error-message">
              <p>{error}</p>
              <button onClick={() => setError('')} className="try-again-btn">Try Again</button>
            </div>
          )}

          {!hasOutput && !isLoading && !error && (
            <div className="empty-state">
              <div className="empty-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                  <path d="M9 22V12h6v10" />
                </svg>
              </div>
              <p>Enter your property details and click Generate</p>
            </div>
          )}

          {isLoading && (
            <div className="loading-state">
              <div className="skeleton-block headline"></div>
              <div className="skeleton-block"></div>
              <div className="skeleton-block"></div>
              <div className="skeleton-block short"></div>
              <p className="loading-text">Crafting your listing...</p>
            </div>
          )}

          {hasOutput && !isLoading && (
            <div className="output-sections">
              {/* Full Listing Description */}
              <div className="output-section">
                <div className="section-header">
                  <h2>Full Listing Description</h2>
                  <div className="section-actions">
                    <button
                      className="action-btn"
                      onClick={() => copyToClipboard(description, 'description')}
                    >
                      {copiedDescription ? 'Copied!' : 'Copy'}
                    </button>
                    <button
                      className="action-btn"
                      onClick={handleRegenerateDescription}
                      disabled={isRegeneratingDescription}
                    >
                      {isRegeneratingDescription ? 'Regenerating...' : 'Regenerate'}
                    </button>
                  </div>
                </div>
                <div className="section-content">
                  {renderMarkdown(description)}
                </div>
              </div>

              {/* Social Media Caption */}
              <div className="output-section">
                <div className="section-header">
                  <h2>Social Media Caption</h2>
                  <div className="section-actions">
                    <button
                      className="action-btn"
                      onClick={() => copyToClipboard(socialCaption, 'social')}
                    >
                      {copiedSocial ? 'Copied!' : 'Copy'}
                    </button>
                    <button
                      className="action-btn"
                      onClick={handleRegenerateSocial}
                      disabled={isRegeneratingSocial}
                    >
                      {isRegeneratingSocial ? 'Regenerating...' : 'Regenerate'}
                    </button>
                  </div>
                </div>
                <div className="section-content social">
                  {renderMarkdown(socialCaption)}
                </div>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  )
}

export default App
