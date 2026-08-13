import { NavLink } from 'react-router-dom'
import { LayoutDashboard, GitBranch, GitPullRequestArrow, Settings, X, GitMerge } from 'lucide-react'
import { useNotifications } from '../../context/NotificationsContext'

const navSections = [
  {
    label: 'Overview',
    items: [{ to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard }],
  },
  {
    label: 'Workspace',
    items: [
      { to: '/repositories', label: 'Repositories', icon: GitBranch, countKey: 'totalRepositories' },
      { to: '/pending-updates', label: 'Pending Updates', icon: GitPullRequestArrow, countKey: 'pendingReviewCount' },
    ],
  },
  {
    label: 'Settings',
    items: [{ to: '/settings', label: 'Account', icon: Settings }],
  },
]

export default function Sidebar({ mobileOpen, onCloseMobile }) {
  const { totalRepositories, pendingReviewCount } = useNotifications()
  const counts = { totalRepositories, pendingReviewCount }

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
          {navSections.map((section) => (
            <div key={section.label} style={styles.section}>
              <div style={styles.sectionLabel}>{section.label}</div>
              {section.items.map(({ to, label, icon: Icon, countKey }) => {
                const count = countKey ? counts[countKey] : null
                return (
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
                    <span style={{ flex: 1 }}>{label}</span>
                    {count !== null && count !== undefined && (
                      <span
                        style={{
                          ...styles.navCount,
                          ...(countKey === 'pendingReviewCount' && count > 0 ? styles.navCountWarn : {}),
                        }}
                      >
                        {count}
                      </span>
                    )}
                  </NavLink>
                )
              })}
            </div>
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
    gap: 16,
    padding: 12,
    flex: 1,
  },
  section: { display: 'flex', flexDirection: 'column', gap: 2 },
  sectionLabel: {
    fontSize: 10.5,
    fontWeight: 700,
    letterSpacing: '0.06em',
    color: 'var(--text-tertiary)',
    textTransform: 'uppercase',
    padding: '4px 12px 6px 12px',
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
  navCount: {
    fontSize: 11.5,
    fontWeight: 700,
    color: 'var(--text-tertiary)',
    background: 'var(--bg-surface-raised)',
    borderRadius: 'var(--radius-full)',
    padding: '1px 7px',
    minWidth: 18,
    textAlign: 'center',
  },
  navCountWarn: {
    color: 'var(--warning)',
    background: 'var(--warning-bg)',
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
