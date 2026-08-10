import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Menu, ChevronDown, LogOut } from 'lucide-react'
import { useAuth } from '../../hooks/useAuth'

export default function Navbar({ onMenuClick, title }) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [menuOpen, setMenuOpen] = useState(false)
  const menuRef = useRef(null)

  useEffect(() => {
    function handleClickOutside(e) {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        setMenuOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <header className="flex h-16 shrink-0 items-center justify-between border-b border-slate-200 bg-surface px-4 lg:px-6">
      <div className="flex items-center gap-3">
        <button
          className="text-navy-800 lg:hidden"
          onClick={onMenuClick}
          aria-label="Ouvrir le menu"
        >
          <Menu size={22} />
        </button>
        {title && (
          <h1 className="font-display text-lg font-semibold text-navy-800">{title}</h1>
        )}
      </div>

      <div className="relative" ref={menuRef}>
        <button
          onClick={() => setMenuOpen((o) => !o)}
          className="flex items-center gap-2.5 rounded-lg px-2 py-1.5 hover:bg-slate-100"
        >
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-indigo-400 text-xs font-semibold text-white">
            {user?.avatarInitials || 'U'}
          </div>
          <span className="hidden text-sm font-medium text-navy-800 sm:block">
            {user?.name || 'Utilisateur'}
          </span>
          <ChevronDown size={15} className="hidden text-ink-muted sm:block" />
        </button>

        {menuOpen && (
          <div className="absolute right-0 mt-2 w-52 rounded-lg border border-slate-200 bg-surface py-1.5 shadow-[var(--shadow-soft)]">
            <div className="border-b border-slate-100 px-3.5 py-2.5">
              <p className="truncate text-sm font-medium text-navy-800">{user?.name}</p>
              <p className="truncate text-xs text-ink-muted">{user?.email}</p>
            </div>
            <button
              onClick={handleLogout}
              className="flex w-full items-center gap-2 px-3.5 py-2.5 text-left text-sm text-coral-500 hover:bg-coral-100"
            >
              <LogOut size={15} />
              Se déconnecter
            </button>
          </div>
        )}
      </div>
    </header>
  )
}
