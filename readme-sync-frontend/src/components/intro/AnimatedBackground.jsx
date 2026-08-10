import { useMemo } from 'react'

/**
 * Lightweight animated background: soft glow blobs + a faint grid + a handful
 * of floating particles. Pure CSS animation (GPU-friendly transform/opacity
 * only) so it stays performant and works even where Framer Motion isn't used.
 */
export default function AnimatedBackground({ intensity = 1 }) {
  const particles = useMemo(() => {
    const count = Math.round(16 * intensity)
    return Array.from({ length: count }, (_, i) => ({
      id: i,
      left: Math.random() * 100,
      top: Math.random() * 100,
      size: 1.5 + Math.random() * 2.5,
      duration: 14 + Math.random() * 16,
      delay: -Math.random() * 20,
    }))
  }, [intensity])

  return (
    <div style={styles.wrap} aria-hidden="true">
      <div style={styles.grid} />
      <div style={{ ...styles.glow, ...styles.glowA }} />
      <div style={{ ...styles.glow, ...styles.glowB }} />
      {particles.map((p) => (
        <div
          key={p.id}
          className="rs-particle"
          style={{
            left: `${p.left}%`,
            top: `${p.top}%`,
            width: p.size,
            height: p.size,
            animationDuration: `${p.duration}s`,
            animationDelay: `${p.delay}s`,
          }}
        />
      ))}
      <div style={styles.vignette} />
    </div>
  )
}

const styles = {
  wrap: {
    position: 'fixed',
    inset: 0,
    overflow: 'hidden',
    background: 'var(--bg-canvas)',
    zIndex: 0,
  },
  grid: {
    position: 'absolute',
    inset: 0,
    backgroundImage:
      'linear-gradient(to right, rgba(255,255,255,0.035) 1px, transparent 1px), linear-gradient(to bottom, rgba(255,255,255,0.035) 1px, transparent 1px)',
    backgroundSize: '46px 46px',
    maskImage: 'radial-gradient(ellipse 70% 60% at 50% 40%, black 40%, transparent 90%)',
    WebkitMaskImage: 'radial-gradient(ellipse 70% 60% at 50% 40%, black 40%, transparent 90%)',
  },
  glow: {
    position: 'absolute',
    borderRadius: '50%',
    filter: 'blur(90px)',
    opacity: 0.16,
  },
  glowA: {
    width: 520,
    height: 520,
    background: 'var(--accent)',
    top: '8%',
    left: '18%',
    animation: 'rs-drift-a 18s ease-in-out infinite',
  },
  glowB: {
    width: 460,
    height: 460,
    background: '#5B9DF9',
    bottom: '4%',
    right: '14%',
    opacity: 0.1,
    animation: 'rs-drift-b 22s ease-in-out infinite',
  },
  vignette: {
    position: 'absolute',
    inset: 0,
    background: 'radial-gradient(ellipse 80% 70% at 50% 45%, transparent 40%, var(--bg-canvas) 92%)',
  },
}
