import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Menu, ChevronDown, LogOut, User, Settings } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'

export default function Topbar({ onOpenMobileMenu, title }) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [menuOpen, setMenuOpen] = useState(false)
  const menuRef = useRef(null)

  useEffect(() => {
    function handleClick(e) {
      if (menuRef.current && !menuRef.current.contains(e.target)) setMenuOpen(false)
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  const initial = user?.email?.[0]?.toUpperCase() || '?'

  return (
    <header style={styles.header}>
      <button className="rs-mobile-menu-btn" style={styles.mobileMenuBtn} onClick={onOpenMobileMenu} aria-label="Open menu">
        <Menu size={20} />
      </button>

      {title && <h1 style={styles.title}>{title}</h1>}

      <div style={{ flex: 1 }} />

      <div ref={menuRef} style={{ position: 'relative' }}>
        <button style={styles.userBtn} onClick={() => setMenuOpen((o) => !o)}>
          <div style={styles.avatar}>{initial}</div>
          <span style={styles.userEmail}>{user?.email}</span>
          <ChevronDown size={14} style={{ color: 'var(--text-tertiary)' }} />
        </button>

        {menuOpen && (
          <div style={styles.dropdown}>
            <div style={styles.dropdownHeader}>
              <div style={styles.dropdownEmail}>{user?.email}</div>
              {user?.github_username && (
                <div style={styles.dropdownSub}>@{user.github_username}</div>
              )}
            </div>
            <button
              style={styles.dropdownItem}
              onClick={() => {
                setMenuOpen(false)
                navigate('/settings')
              }}
            >
              <Settings size={15} />
              Account settings
            </button>
            <button
              style={{ ...styles.dropdownItem, color: 'var(--danger)' }}
              onClick={() => {
                setMenuOpen(false)
                logout()
                navigate('/login')
              }}
            >
              <LogOut size={15} />
              Log out
            </button>
          </div>
        )}
      </div>
    </header>
  )
}

const styles = {
  header: {
    height: 'var(--topbar-height)',
    borderBottom: '1px solid var(--border-subtle)',
    display: 'flex',
    alignItems: 'center',
    padding: '0 20px',
    gap: 12,
    position: 'sticky',
    top: 0,
    background: 'var(--bg-canvas)',
    zIndex: 50,
  },
  mobileMenuBtn: {
    display: 'none',
    background: 'none',
    border: 'none',
    color: 'var(--text-secondary)',
    padding: 6,
  },
  title: { fontSize: 15, fontWeight: 700, color: 'var(--text-primary)' },
  userBtn: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    background: 'none',
    border: '1px solid transparent',
    padding: '6px 8px',
    borderRadius: 'var(--radius-sm)',
  },
  avatar: {
    width: 26,
    height: 26,
    borderRadius: '50%',
    background: 'var(--accent-bg)',
    color: 'var(--accent)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: 12,
    fontWeight: 700,
    flexShrink: 0,
  },
  userEmail: { fontSize: 13, color: 'var(--text-secondary)', fontWeight: 500 },
  dropdown: {
    position: 'absolute',
    top: '110%',
    right: 0,
    width: 220,
    background: 'var(--bg-surface-raised)',
    border: '1px solid var(--border-default)',
    borderRadius: 'var(--radius-md)',
    boxShadow: 'var(--shadow-lg)',
    padding: 6,
    zIndex: 200,
  },
  dropdownHeader: {
    padding: '8px 10px',
    borderBottom: '1px solid var(--border-subtle)',
    marginBottom: 6,
  },
  dropdownEmail: { fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' },
  dropdownSub: { fontSize: 12, color: 'var(--text-tertiary)', marginTop: 2 },
  dropdownItem: {
    display: 'flex',
    alignItems: 'center',
    gap: 9,
    width: '100%',
    padding: '8px 10px',
    background: 'none',
    border: 'none',
    borderRadius: 6,
    fontSize: 13,
    fontWeight: 500,
    color: 'var(--text-secondary)',
    textAlign: 'left',
  },
}
