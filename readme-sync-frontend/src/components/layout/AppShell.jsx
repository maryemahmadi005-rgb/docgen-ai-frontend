import { useState } from 'react'
import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'
import Topbar from './Topbar'

export default function AppShell() {
  const [mobileOpen, setMobileOpen] = useState(false)

  return (
    <div style={styles.shell}>
      <Sidebar mobileOpen={mobileOpen} onCloseMobile={() => setMobileOpen(false)} />
      <div style={styles.main} className="rs-main">
        <Topbar onOpenMobileMenu={() => setMobileOpen(true)} />
        <div className="rs-content-padding" style={styles.content}>
          <Outlet />
        </div>
      </div>
    </div>
  )
}

const styles = {
  shell: {
    display: 'flex',
    minHeight: '100vh',
    background: 'var(--bg-canvas)',
  },
  main: {
    flex: 1,
    marginLeft: 'var(--sidebar-width)',
    minWidth: 0,
    display: 'flex',
    flexDirection: 'column',
  },
  content: {
    flex: 1,
    padding: '28px 32px 60px 32px',
    maxWidth: 1280,
    width: '100%',
    margin: '0 auto',
    boxSizing: 'border-box',
  },
}
