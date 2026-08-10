import { NavLink } from 'react-router-dom'
import { LayoutDashboard, GitBranch, GitPullRequestArrow, Settings, X, GitMerge } from 'lucide-react'

const navItems = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/repositories', label: 'Repositories', icon: GitBranch },
  { to: '/pending-updates', label: 'Pending Updates', icon: GitPullRequestArrow },
  { to: '/settings', label: 'Account', icon: Settings },
]

export default function Sidebar({ mobileOpen, onCloseMobile }) {
  return (
    <>
      {mobileOpen && <div className="rs-mobile-overlay" style={{ display: 'none' }} onClick={onCloseMobile} />}
      <aside
        data-sidebar
        className={mobileOpen ? 'mobile-open' : ''}
        style={styles.sidebar}
      >
        <div style={styles.brand}>
          <div style={styles.brandMark}>
            <GitMerge size={16} strokeWidth={2.5} />
          </div>
          <span style={styles.brandText}>README Sync</span>
          <button className="rs-mobile-close-btn" style={styles.mobileCloseBtn} onClick={onCloseMobile} aria-label="Close menu">
            <X size={18} />
          </button>
        </div>

        <nav style={styles.nav}>
          {navItems.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              onClick={onCloseMobile}
              style={({ isActive }) => ({
                ...styles.navItem,
                ...(isActive ? styles.navItemActive : {}),
              })}
            >
              <Icon size={17} strokeWidth={2} />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>

        <div style={styles.footer}>
          <div style={styles.footerText}>README Sync Platform v1.0</div>
        </div>
      </aside>
    </>
  )
}

const styles = {
  sidebar: {
    position: 'fixed',
    top: 0,
    left: 0,
    bottom: 0,
    width: 'var(--sidebar-width)',
    background: 'var(--bg-surface)',
    borderRight: '1px solid var(--border-subtle)',
    display: 'flex',
    flexDirection: 'column',
    zIndex: 100,
    transition: 'transform 0.2s ease',
  },
  brand: {
    display: 'flex',
    alignItems: 'center',
    gap: 10,
    padding: '18px 20px',
    borderBottom: '1px solid var(--border-subtle)',
    height: 'var(--topbar-height)',
    boxSizing: 'border-box',
  },
  brandMark: {
    width: 26,
    height: 26,
    borderRadius: 7,
    background: 'var(--accent)',
    color: '#04120D',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
  },
  brandText: {
    fontSize: 14.5,
    fontWeight: 700,
    letterSpacing: '-0.02em',
    color: 'var(--text-primary)',
  },
  mobileCloseBtn: {
    display: 'none',
    marginLeft: 'auto',
    background: 'none',
    border: 'none',
    color: 'var(--text-secondary)',
  },
  nav: {
    display: 'flex',
    flexDirection: 'column',
    gap: 2,
    padding: 12,
    flex: 1,
  },
  navItem: {
    display: 'flex',
    alignItems: 'center',
    gap: 10,
    padding: '9px 12px',
    borderRadius: 'var(--radius-sm)',
    color: 'var(--text-secondary)',
    fontSize: 13.5,
    fontWeight: 500,
    transition: 'background 0.12s ease, color 0.12s ease',
  },
  navItemActive: {
    background: 'var(--accent-bg)',
    color: 'var(--accent)',
    fontWeight: 600,
  },
  footer: {
    padding: '14px 20px',
    borderTop: '1px solid var(--border-subtle)',
  },
  footerText: {
    fontSize: 11.5,
    color: 'var(--text-tertiary)',
  },
}
