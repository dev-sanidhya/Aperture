import ScrollStorySection from './components/ScrollStorySection'

function App() {
  return (
    <div>
      <div
        style={{
          height: '100vh',
          background: '#0a0d12',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '16px',
        }}
      >
        <div
          style={{
            fontSize: '11px',
            letterSpacing: '0.16em',
            textTransform: 'uppercase',
            color: '#d1a26a',
            fontFamily: 'Manrope, sans-serif',
          }}
        >
          Aperture — Scroll Preview
        </div>
        <h1
          style={{
            fontFamily: '"Cormorant Garamond", serif',
            fontSize: 'clamp(2.5rem, 6vw, 5rem)',
            color: '#f5f1e8',
            fontWeight: 600,
            textAlign: 'center',
          }}
        >
          Scroll down ↓
        </h1>
        <p style={{ color: 'rgba(245,241,232,0.45)', fontFamily: 'Manrope, sans-serif', fontSize: '0.9rem' }}>
          The storytelling section begins below
        </p>
      </div>

      <ScrollStorySection />

      <div
        style={{
          height: '50vh',
          background: '#0a0d12',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <p
          style={{
            color: 'rgba(245,241,232,0.3)',
            fontFamily: 'Manrope, sans-serif',
            fontSize: '0.85rem',
            letterSpacing: '0.1em',
          }}
        >
          End of section
        </p>
      </div>
    </div>
  )
}

export default App
