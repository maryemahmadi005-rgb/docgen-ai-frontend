import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  GitMerge, GitBranch, GitPullRequestArrow, RefreshCw, ShieldCheck,
  FileText, ArrowRight, CheckCircle2, History,
} from 'lucide-react'

const fadeUp = {
  hidden: { opacity: 0, y: 16 },
  show: { opacity: 1, y: 0, transition: { duration: 0.5 } },
}

export default function LandingPage() {
  return (
    <div style={styles.page}>
      <header style={styles.navbar}>
        <div style={{ ...styles.container, ...styles.navInner }}>
          <div style={styles.brand}>
            <div style={styles.brandMark}>
              <GitMerge size={16} strokeWidth={2.5} />
            </div>
            README Sync
          </div>
          <nav style={styles.navLinks} className="rs-hide-mobile">
            <a href="#features" style={styles.navLink}>Features</a>
            <a href="#workflow" style={styles.navLink}>Workflow</a>
          </nav>
          <div style={{ display: 'flex', gap: 10 }}>
            <Link to="/login" style={styles.navBtnGhost}>Sign in</Link>
            <Link to="/register" style={styles.navBtnPrimary}>Get started</Link>
          </div>
        </div>
      </header>

      {/* HERO */}
      <section style={styles.hero}>
        <div style={styles.container}>
          <motion.div initial="hidden" animate="show" variants={fadeUp} style={styles.heroBadge}>
            <GitBranch size={13} />
            Documentation that follows your code
          </motion.div>
          <motion.h1
            initial="hidden"
            animate="show"
            variants={fadeUp}
            transition={{ delay: 0.05 }}
            style={styles.heroTitle}
          >
            Keep your README<br />
            <span style={styles.heroTitleAccent}>in sync with your code.</span>
          </motion.h1>
          <motion.p
            initial="hidden"
            animate="show"
            variants={fadeUp}
            transition={{ delay: 0.1 }}
            style={styles.heroSubtitle}
          >
            README Sync tracks changes in your repository, proposes documentation
            updates section by section, and lets you approve every change before
            it reaches your codebase — or automate it entirely.
          </motion.p>
          <motion.div
            initial="hidden"
            animate="show"
            variants={fadeUp}
            transition={{ delay: 0.15 }}
            style={styles.heroActions}
          >
            <Link to="/register" style={styles.heroPrimaryBtn}>
              Get started <ArrowRight size={16} />
            </Link>
            <Link to="/login" style={styles.heroSecondaryBtn}>
              Sign in
            </Link>
          </motion.div>
        </div>
      </section>

      {/* PROBLEM / SOLUTION */}
      <section style={styles.section}>
        <div style={styles.container}>
          <div style={styles.twoCol}>
            <div>
              <div style={styles.eyebrow}>The problem</div>
              <h3 style={styles.sectionTitle}>Documentation drifts. Every team knows it.</h3>
              <p style={styles.sectionText}>
                Code evolves fast. READMEs don't. Install steps go stale, feature
                lists fall behind, and new contributors inherit documentation
                nobody trusts anymore.
              </p>
            </div>
            <div>
              <div style={styles.eyebrow}>The approach</div>
              <h3 style={styles.sectionTitle}>Section-level updates, reviewed by you.</h3>
              <p style={styles.sectionText}>
                Instead of regenerating your README from scratch, changes are
                proposed section by section — tied to the exact commit that
                triggered them — so you always know what changed and why.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* WORKFLOW */}
      <section id="workflow" style={styles.sectionAlt}>
        <div style={styles.container}>
          <div style={styles.eyebrow}>How it works</div>
          <h2 style={styles.sectionTitleLg}>Three steps to synchronized docs</h2>
          <div style={styles.stepsGrid}>
            {[
              { icon: GitBranch, step: '01', title: 'Connect a repository', text: 'Track a GitHub repository and its branch.' },
              { icon: GitPullRequestArrow, step: '02', title: 'Review proposed updates', text: 'Every detected change becomes a reviewable README proposal.' },
              { icon: CheckCircle2, step: '03', title: 'Approve or automate', text: 'Approve manually, or switch to automatic sync when you trust the flow.' },
            ].map(({ icon: Icon, step, title, text }) => (
              <div key={step} style={styles.stepCard}>
                <div style={styles.stepIcon}><Icon size={18} /></div>
                <div style={styles.stepNumber}>{step}</div>
                <h4 style={styles.stepTitle}>{title}</h4>
                <p style={styles.stepText}>{text}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* FEATURES */}
      <section id="features" style={styles.section}>
        <div style={styles.container}>
          <div style={styles.eyebrow}>Features</div>
          <h2 style={styles.sectionTitleLg}>Built for real engineering workflows</h2>
          <div style={styles.featuresGrid}>
            {[
              { icon: RefreshCw, title: 'Manual or automatic sync', text: 'Choose whether changes apply immediately or wait for your approval.' },
              { icon: History, title: 'Full version history', text: 'Every README version is preserved and restorable at any time.' },
              { icon: ShieldCheck, title: 'Reviewed, not guessed', text: 'Pending updates show exactly which sections changed and from which commit.' },
              { icon: FileText, title: 'Section-aware editing', text: 'Edit your README directly with Markdown and structured sections.' },
            ].map(({ icon: Icon, title, text }) => (
              <div key={title} style={styles.featureCard}>
                <div style={styles.featureIcon}><Icon size={17} /></div>
                <h4 style={styles.featureTitle}>{title}</h4>
                <p style={styles.featureText}>{text}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section style={styles.cta}>
        <div style={styles.container}>
          <h2 style={styles.ctaTitle}>Start syncing your documentation today</h2>
          <p style={styles.ctaSubtitle}>Free to start. No credit card required.</p>
          <Link to="/register" style={styles.heroPrimaryBtn}>
            Create your account <ArrowRight size={16} />
          </Link>
        </div>
      </section>

      <footer style={styles.footer}>
        <div style={{ ...styles.container, ...styles.footerInner }}>
          <div style={styles.brand}>
            <div style={styles.brandMark}><GitMerge size={14} strokeWidth={2.5} /></div>
            README Sync
          </div>
          <span style={styles.footerText}>© {new Date().getFullYear()} README Sync Platform</span>
        </div>
      </footer>
    </div>
  )
}

const styles = {
  page: { background: 'var(--bg-canvas)', color: 'var(--text-primary)' },
  container: { maxWidth: 1080, margin: '0 auto', padding: '0 24px' },
  navbar: { borderBottom: '1px solid var(--border-subtle)', position: 'sticky', top: 0, background: 'rgba(10,11,13,0.85)', backdropFilter: 'blur(8px)', zIndex: 50 },
  navInner: { height: 64, display: 'flex', alignItems: 'center', gap: 24 },
  brand: { display: 'flex', alignItems: 'center', gap: 9, fontSize: 14.5, fontWeight: 700 },
  brandMark: { width: 26, height: 26, borderRadius: 7, background: 'var(--accent)', color: '#04120D', display: 'flex', alignItems: 'center', justifyContent: 'center' },
  navLinks: { display: 'flex', gap: 22, flex: 1, marginLeft: 12 },
  navLink: { fontSize: 13.5, color: 'var(--text-secondary)', fontWeight: 500 },
  navBtnGhost: { fontSize: 13.5, fontWeight: 600, color: 'var(--text-secondary)', padding: '8px 14px' },
  navBtnPrimary: { fontSize: 13.5, fontWeight: 600, color: '#04120D', background: 'var(--accent)', padding: '8px 16px', borderRadius: 'var(--radius-sm)' },

  hero: { padding: '96px 0 80px 0', textAlign: 'center' },
  heroBadge: { display: 'inline-flex', alignItems: 'center', gap: 7, fontSize: 12.5, fontWeight: 600, color: 'var(--accent)', background: 'var(--accent-bg)', border: '1px solid var(--accent-border)', padding: '6px 13px', borderRadius: 999, marginBottom: 24 },
  heroTitle: { fontSize: 'clamp(32px, 5.5vw, 54px)', fontWeight: 800, letterSpacing: '-0.04em', lineHeight: 1.1 },
  heroTitleAccent: { color: 'var(--accent)' },
  heroSubtitle: { fontSize: 16.5, color: 'var(--text-secondary)', maxWidth: 620, margin: '22px auto 0 auto', lineHeight: 1.6 },
  heroActions: { display: 'flex', gap: 12, justifyContent: 'center', marginTop: 32, flexWrap: 'wrap' },
  heroPrimaryBtn: { display: 'inline-flex', alignItems: 'center', gap: 8, fontSize: 14.5, fontWeight: 700, color: '#04120D', background: 'var(--accent)', padding: '12px 22px', borderRadius: 'var(--radius-sm)' },
  heroSecondaryBtn: { display: 'inline-flex', alignItems: 'center', fontSize: 14.5, fontWeight: 600, color: 'var(--text-primary)', background: 'var(--bg-surface-raised)', border: '1px solid var(--border-default)', padding: '12px 22px', borderRadius: 'var(--radius-sm)' },

  section: { padding: '72px 0' },
  sectionAlt: { padding: '72px 0', background: 'var(--bg-surface)', borderTop: '1px solid var(--border-subtle)', borderBottom: '1px solid var(--border-subtle)' },
  twoCol: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 48 },
  eyebrow: { fontSize: 12.5, fontWeight: 700, color: 'var(--accent)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 12 },
  sectionTitle: { fontSize: 22, fontWeight: 800, letterSpacing: '-0.02em', marginBottom: 12 },
  sectionTitleLg: { fontSize: 30, fontWeight: 800, letterSpacing: '-0.03em', marginBottom: 40 },
  sectionText: { fontSize: 14.5, color: 'var(--text-secondary)', lineHeight: 1.7 },

  stepsGrid: { display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 20 },
  stepCard: { background: 'var(--bg-canvas)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-lg)', padding: 24 },
  stepIcon: { width: 38, height: 38, borderRadius: 10, background: 'var(--accent-bg)', color: 'var(--accent)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 20 },
  stepNumber: { fontSize: 12, fontWeight: 700, color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)', marginBottom: 8 },
  stepTitle: { fontSize: 16, fontWeight: 700, marginBottom: 8 },
  stepText: { fontSize: 13.5, color: 'var(--text-secondary)', lineHeight: 1.6 },

  featuresGrid: { display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 16 },
  featureCard: { border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-md)', padding: 22 },
  featureIcon: { width: 34, height: 34, borderRadius: 9, background: 'var(--bg-surface-raised)', color: 'var(--accent)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 16 },
  featureTitle: { fontSize: 15, fontWeight: 700, marginBottom: 6 },
  featureText: { fontSize: 13.5, color: 'var(--text-secondary)', lineHeight: 1.6 },

  cta: { padding: '80px 0', textAlign: 'center', borderTop: '1px solid var(--border-subtle)' },
  ctaTitle: { fontSize: 28, fontWeight: 800, letterSpacing: '-0.03em' },
  ctaSubtitle: { fontSize: 14.5, color: 'var(--text-secondary)', margin: '12px 0 28px 0' },

  footer: { borderTop: '1px solid var(--border-subtle)', padding: '24px 0' },
  footerInner: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 },
  footerText: { fontSize: 12.5, color: 'var(--text-tertiary)' },
}
