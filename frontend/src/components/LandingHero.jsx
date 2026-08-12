import React from 'react';

/**
 * LandingHero — the opening splash page for CodeOracle.
 * Features:
 *  - Notebook-grid background (Uiverse.io by kennyotsu-monochromia)
 *  - Three overlapping glass cards that fan out on hover (Uiverse.io by codebykay101)
 *    Cards: Github · Code · Learn
 *  - Prominent "CodeOracle" title + tagline
 *  - CTA button to proceed to the Upload page
 */
export function LandingHero({ onEnter, themeMode }) {
  const isFun = themeMode === 'fun';

  return (
    <div
      className="landing-hero"
      style={{
        width: '100%',
        minHeight: 'calc(100vh - 3.5rem)',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        position: 'relative',
        overflow: 'hidden',
        /* Grid background from kennyotsu-monochromia */
        '--grid-color': isFun ? '#d1d5db' : '#1e2733',
        backgroundColor: isFun ? '#FFFBEB' : '#0D1117',
        backgroundImage: `
          linear-gradient(0deg, transparent 24%, var(--grid-color) 25%, var(--grid-color) 26%, transparent 27%, transparent 74%, var(--grid-color) 75%, var(--grid-color) 76%, transparent 77%, transparent),
          linear-gradient(90deg, transparent 24%, var(--grid-color) 25%, var(--grid-color) 26%, transparent 27%, transparent 74%, var(--grid-color) 75%, var(--grid-color) 76%, transparent 77%, transparent)
        `,
        backgroundSize: '55px 55px',
      }}
    >
      {/* Radial glow behind the title */}
      <div
        style={{
          position: 'absolute',
          width: '600px',
          height: '600px',
          borderRadius: '50%',
          background: isFun
            ? 'radial-gradient(circle, rgba(229,57,53,0.15) 0%, transparent 70%)'
            : 'radial-gradient(circle, rgba(88,166,255,0.08) 0%, transparent 70%)',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -55%)',
          pointerEvents: 'none',
        }}
      />

      {/* Title Block */}
      <div style={{ textAlign: 'center', zIndex: 2, marginBottom: '48px' }}>
        <h1
          className="landing-title"
          style={{
            fontSize: '56px',
            fontWeight: 900,
            letterSpacing: '-0.03em',
            lineHeight: 1.1,
            color: isFun ? '#212121' : '#E6EDF3',
            fontFamily: "'Inter', system-ui, sans-serif",
            margin: 0,
          }}
        >
          Code<span style={{ color: isFun ? '#E53935' : '#58A6FF' }}>Oracle</span>
        </h1>

        <p
          style={{
            marginTop: '12px',
            fontSize: '15px',
            fontWeight: 500,
            color: isFun ? '#374151' : '#8B949E',
            maxWidth: '460px',
            lineHeight: 1.5,
          }}
        >
          Enterprise Code Intelligence — understand, graph, test, and modernize legacy codebases in minutes.
        </p>
      </div>

      {/* Glass Cards Fan (codebykay101 Uiverse) */}
      <div className="glass-container" style={{ zIndex: 2, marginBottom: '48px' }}>
        {/* Github Card */}
        <div className="glass-card" data-text="Github" style={{ '--r': '-15' }}>
          <svg viewBox="0 0 496 512" height="1em" xmlns="http://www.w3.org/2000/svg">
            <path d="M165.9 397.4c0 2-2.3 3.6-5.2 3.6-3.3.3-5.6-1.3-5.6-3.6 0-2 2.3-3.6 5.2-3.6 3-.3 5.6 1.3 5.6 3.6zm-31.1-4.5c-.7 2 1.3 4.3 4.3 4.9 2.6 1 5.6 0 6.2-2s-1.3-4.3-4.3-5.2c-2.6-.7-5.5.3-6.2 2.3zm44.2-1.7c-2.9.7-4.9 2.6-4.6 4.9.3 2 2.9 3.3 5.9 2.6 2.9-.7 4.9-2.6 4.6-4.6-.3-1.9-3-3.2-5.9-2.9zM244.8 8C106.1 8 0 113.3 0 252c0 110.9 69.8 205.8 169.5 239.2 12.8 2.3 17.3-5.6 17.3-12.1 0-6.2-.3-40.4-.3-61.4 0 0-70 15-84.7-29.8 0 0-11.4-29.1-27.8-36.6 0 0-22.9-15.7 1.6-15.4 0 0 24.9 2 38.6 25.8 21.9 38.6 58.6 27.5 72.9 20.9 2.3-16 8.8-27.1 16-33.7-55.9-6.2-112.3-14.3-112.3-110.5 0-27.5 7.6-41.3 23.6-58.9-2.6-6.5-11.1-33.3 2.6-67.9 20.9-6.5 69 27 69 27 20-5.6 41.5-8.5 62.8-8.5s42.8 2.9 62.8 8.5c0 0 48.1-33.6 69-27 13.7 34.7 5.2 61.4 2.6 67.9 16 17.7 25.8 31.5 25.8 58.9 0 96.5-58.9 104.2-114.8 110.5 9.2 7.9 17 22.9 17 46.4 0 33.7-.3 75.4-.3 83.6 0 6.5 4.6 14.4 17.3 12.1C428.2 457.8 496 362.9 496 252 496 113.3 383.5 8 244.8 8zM97.2 352.9c-1.3 1-1 3.3.7 5.2 1.6 1.6 3.9 2.3 5.2 1 1.3-1 1-3.3-.7-5.2-1.6-1.6-3.9-2.3-5.2-1zm-10.8-8.1c-.7 1.3.3 2.9 2.3 3.9 1.6 1 3.6.7 4.3-.7.7-1.3-.3-2.9-2.3-3.9-2-.6-3.6-.3-4.3.7zm32.4 35.6c-1.6 1.3-1 4.3 1.3 6.2 2.3 2.3 5.2 2.6 6.5 1 1.3-1.3.7-4.3-1.3-6.2-2.2-2.3-5.2-2.6-6.5-1zm-11.4-14.7c-1.6 1-1.6 3.6 0 5.9 1.6 2.3 4.3 3.3 5.6 2.3 1.6-1.3 1.6-3.9 0-6.2-1.4-2.3-4-3.3-5.6-2z" />
          </svg>
        </div>

        {/* Code Card */}
        <div className="glass-card" data-text="Code" style={{ '--r': '5' }}>
          <svg viewBox="0 0 640 512" height="1em" xmlns="http://www.w3.org/2000/svg">
            <path d="M392.8 1.2c-17-4.9-34.7 5-39.6 22l-128 448c-4.9 17 5 34.7 22 39.6s34.7-5 39.6-22l128-448c4.9-17-5-34.7-22-39.6zm80.6 120.1c-12.5 12.5-12.5 32.8 0 45.3L562.7 256l-89.4 89.4c-12.5 12.5-12.5 32.8 0 45.3s32.8 12.5 45.3 0l112-112c12.5-12.5 12.5-32.8 0-45.3l-112-112c-12.5-12.5-32.8-12.5-45.3 0zm-306.7 0c-12.5-12.5-32.8-12.5-45.3 0l-112 112c-12.5 12.5-12.5 32.8 0 45.3l112 112c12.5 12.5 32.8 12.5 45.3 0s12.5-32.8 0-45.3L77.3 256l89.4-89.4c12.5-12.5 12.5-32.8 0-45.3z" />
          </svg>
        </div>

        {/* Learn Card */}
        <div className="glass-card" data-text="Learn" style={{ '--r': '25' }}>
          <svg viewBox="0 0 576 512" height="1em" xmlns="http://www.w3.org/2000/svg">
            <path d="M542.22 32.05c-54.8 3.11-163.72 14.43-230.96 55.59-4.64 2.84-7.27 7.89-7.27 13.17v363.87c0 11.55 12.63 18.85 23.28 13.49 69.18-34.82 169.23-44.32 218.7-46.92 16.89-.89 30.02-14.43 30.02-30.66V62.75c.01-17.71-15.35-31.74-33.77-30.7zM264.73 87.64C197.5 46.48 88.58 35.17 33.78 32.05 15.36 31.01 0 45.04 0 62.75V400.6c0 16.24 13.13 29.78 30.02 30.66 49.49 2.6 149.59 12.11 218.77 46.95 10.62 5.35 23.21-1.94 23.21-13.46V100.63c0-5.29-2.62-10.14-7.27-12.99z" />
          </svg>
        </div>
      </div>

      {/* CTA Button to Enter */}
      <button
        onClick={onEnter}
        className="landing-cta"
        style={{
          zIndex: 2,
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          padding: '14px 36px',
          fontSize: '14px',
          fontWeight: 800,
          fontFamily: "'Inter', system-ui, sans-serif",
          letterSpacing: '0.5px',
          borderRadius: isFun ? '50px' : '6px',
          cursor: 'pointer',
          transition: 'all 0.35s cubic-bezier(0.23, 1, 0.32, 1)',
          border: isFun ? '3px solid #000' : '2px solid #30363D',
          background: isFun ? '#FDD835' : '#58A6FF',
          color: isFun ? '#000' : '#0D1117',
          boxShadow: isFun ? '5px 5px 0px #000' : '0 4px 24px rgba(88,166,255,0.25)',
          textTransform: 'uppercase',
        }}
      >
        <span>{isFun ? '🚀 Lets Go!' : 'Get Started'}</span>
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
          <line x1="5" y1="12" x2="19" y2="12" />
          <polyline points="12 5 19 12 12 19" />
        </svg>
      </button>

      {/* Subtle bottom badge */}
      <p
        style={{
          position: 'absolute',
          bottom: '24px',
          fontSize: '11px',
          fontFamily: "'JetBrains Mono', monospace",
          color: isFun ? '#9CA3AF' : '#484F58',
          letterSpacing: '0.05em',
          zIndex: 2,
        }}
      >
        {isFun ? '★ Built with ❤️ for HackOrbit ★' : 'Enterprise Code Intelligence Platform'}
      </p>
    </div>
  );
}
