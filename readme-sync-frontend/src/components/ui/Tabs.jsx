import { NavLink } from 'react-router-dom'

export default function Tabs({ items }) {
  return (
    <div style={styles.wrap} className="rs-tabs-scroll">
      {items.map(({ to, label, icon: Icon, end }) => (
        <NavLink
          key={to}
          to={to}
          end={end}
          style={({ isActive }) => ({
            ...styles.tab,
            ...(isActive ? styles.tabActive : {}),
          })}
        >
          {Icon && <Icon size={14.5} />}
          {label}
        </NavLink>
      ))}
    </div>
  )
}

const styles = {
  wrap: {
    display: 'flex',
    gap: 4,
    borderBottom: '1px solid var(--border-subtle)',
    marginBottom: 24,
    overflowX: 'auto',
  },
  tab: {
    display: 'flex',
    alignItems: 'center',
    gap: 6,
    padding: '10px 14px',
    fontSize: 13.5,
    fontWeight: 600,
    color: 'var(--text-tertiary)',
    borderBottom: '2px solid transparent',
    whiteSpace: 'nowrap',
    marginBottom: -1,
  },
  tabActive: {
    color: 'var(--text-primary)',
    borderBottomColor: 'var(--accent)',
  },
}
