export default function PageHeader({ title, description, actions }) {
  return (
    <div style={styles.wrap} className="rs-stack-mobile">
      <div>
        <h1 style={styles.title}>{title}</h1>
        {description && <p style={styles.description}>{description}</p>}
      </div>
      {actions && <div style={styles.actions}>{actions}</div>}
    </div>
  )
}

const styles = {
  wrap: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    gap: 16,
    marginBottom: 24,
  },
  title: { fontSize: 22, fontWeight: 800, letterSpacing: '-0.03em', color: 'var(--text-primary)' },
  description: { fontSize: 13.5, color: 'var(--text-secondary)', marginTop: 6 },
  actions: { display: 'flex', gap: 8, flexShrink: 0 },
}
