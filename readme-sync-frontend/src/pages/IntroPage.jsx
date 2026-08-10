import { useEffect, useState, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { GitMerge, ArrowRight } from 'lucide-react'
import AnimatedBackground from '../components/intro/AnimatedBackground'
import FlowDiagram from '../components/intro/FlowDiagram'

const BRAND_NAME = 'README Sync'
const TAGLINE = 'Keep your documentation in sync with your code.'

export default function IntroPage() {
  const navigate = useNavigate()
  const [phase, setPhase] = useState('logo') // logo -> flow -> tagline -> cta
  const [exiting, setExiting] = useState(false)

  const reducedMotion = useMemo(
    () => window.matchMedia?.('(prefers-reduced-motion: reduce)').matches,
    []
  )

  useEffect(() => {
    if (reducedMotion) {
      setPhase('cta')
      return
    }
    const t1 = setTimeout(() => setPhase('flow'), 900)
    const t2 = setTimeout(() => setPhase('tagline'), 900 + 1550)
    const t3 = setTimeout(() => setPhase('cta'), 900 + 1550 + 500)
    return () => {
      clearTimeout(t1)
      clearTimeout(t2)
      clearTimeout(t3)
    }
  }, [reducedMotion])

  function handleGetStarted() {
    sessionStorage.setItem('rs_intro_seen', '1')
    setExiting(true)
    setTimeout(() => navigate('/login', { state: { fromIntro: true } }), 480)
  }

  function handleSkip() {
    sessionStorage.setItem('rs_intro_seen', '1')
    navigate('/login', { state: { fromIntro: true } })
  }

  const flowActive = phase === 'flow' || phase === 'tagline' || phase === 'cta'

  return (
    <AnimatePresence>
      {!exiting && (
        <motion.div
          key="intro"
          exit={{ opacity: 0, scale: 1.02 }}
          transition={{ duration: 0.45, ease: 'easeInOut' }}
          style={styles.page}
        >
          <AnimatedBackground />

          <button onClick={handleSkip} style={styles.skipBtn}>
            Skip
          </button>

          <div style={styles.content}>
            <motion.div
              initial={{ opacity: 0, y: 14 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
              style={styles.brandRow}
            >
              <motion.div
                initial={{ scale: 0.5, rotate: -8, opacity: 0 }}
                animate={{ scale: 1, rotate: 0, opacity: 1 }}
                transition={{ duration: 0.55, ease: [0.16, 1, 0.3, 1] }}
                style={styles.logoMark}
              >
                <GitMerge size={22} strokeWidth={2.5} />
              </motion.div>
              <div style={styles.brandTextWrap}>
                {BRAND_NAME.split('').map((char, i) => (
                  <motion.span
                    key={i}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.35 + i * 0.028, duration: 0.4 }}
                    style={styles.brandChar}
                    className="rs-intro-brand-char"
                  >
                    {char === ' ' ? '\u00A0' : char}
                  </motion.span>
                ))}
              </div>
            </motion.div>

            <div style={styles.flowWrap}>
              <FlowDiagram active={flowActive} />
            </div>

            <AnimatePresence>
              {(phase === 'tagline' || phase === 'cta') && (
                <motion.p
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
                  style={styles.tagline}
                >
                  {TAGLINE}
                </motion.p>
              )}
            </AnimatePresence>

            <AnimatePresence>
              {phase === 'cta' && (
                <motion.div
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
                  style={styles.ctaWrap}
                >
                  <button onClick={handleGetStarted} style={styles.ctaBtn}>
                    Get started
                    <ArrowRight size={16} />
                  </button>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}

const styles = {
  page: {
    position: 'fixed',
    inset: 0,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 10,
    overflow: 'hidden',
  },
  skipBtn: {
    position: 'absolute',
    top: 24,
    right: 24,
    fontSize: 12.5,
    fontWeight: 600,
    color: 'var(--text-tertiary)',
    background: 'var(--bg-surface)',
    border: '1px solid var(--border-subtle)',
    padding: '7px 14px',
    borderRadius: 'var(--radius-full)',
    zIndex: 2,
  },
  content: {
    position: 'relative',
    zIndex: 1,
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    padding: '0 24px',
    maxWidth: 640,
    width: '100%',
  },
  brandRow: {
    display: 'flex',
    alignItems: 'center',
    gap: 14,
    marginBottom: 56,
  },
  logoMark: {
    width: 44,
    height: 44,
    borderRadius: 12,
    background: 'var(--accent)',
    color: '#04120D',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    boxShadow: '0 0 32px rgba(0,217,163,0.35)',
    flexShrink: 0,
  },
  brandTextWrap: {
    display: 'flex',
  },
  brandChar: {
    fontSize: 26,
    fontWeight: 800,
    letterSpacing: '-0.03em',
    color: 'var(--text-primary)',
    display: 'inline-block',
  },
  flowWrap: {
    marginBottom: 40,
    width: '100%',
    display: 'flex',
    justifyContent: 'center',
    minHeight: 90,
  },
  tagline: {
    fontSize: 15.5,
    color: 'var(--text-secondary)',
    textAlign: 'center',
    lineHeight: 1.6,
    maxWidth: 380,
    marginBottom: 32,
  },
  ctaWrap: {
    display: 'flex',
  },
  ctaBtn: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: 8,
    fontSize: 14.5,
    fontWeight: 700,
    color: '#04120D',
    background: 'var(--accent)',
    padding: '13px 26px',
    borderRadius: 'var(--radius-sm)',
    boxShadow: '0 0 28px rgba(0,217,163,0.28)',
    border: 'none',
  },
}
