import { Mail, Github, LogOut } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import { useNavigate } from 'react-router-dom'
import { Card, Badge } from '../../components/ui/Primitives'
import Button from '../../components/ui/Button'
import PageHeader from '../../components/ui/PageHeader'

export default function AccountSettingsPage() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  function handleLogout() {
    logout()
    navigate('/login')
  }

  return (
    <div style={{ maxWidth: 560 }}>
      <PageHeader title="Account" description="Manage your account and connections." />

      <Card style={{ marginBottom: 14 }}>
        <div style={styles.row}>
          <div style={styles.rowIcon}><Mail size={16} /></div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={styles.rowLabel}>Email</div>
            <div style={styles.rowValue}>{user?.email}</div>
          </div>
        </div>
      </Card>

      <Card style={{ marginBottom: 14 }}>
        <div style={styles.row}>
          <div style={styles.rowIcon}><Github size={16} /></div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={styles.rowLabel}>GitHub</div>
            <div style={styles.rowValue}>
              {user?.github_username ? `@${user.github_username}` : 'Not connected'}
            </div>
          </div>
          <Badge variant={user?.github_username ? 'success' : 'neutral'} dot>
            {user?.github_username ? 'Connected' : 'Not connected'}
          </Badge>
        </div>
        {!user?.github_username && (
          <p style={styles.note}>
            GitHub connection isn't available from the account settings yet — this section
            will update automatically once a connection exists on your account.
          </p>
        )}
      </Card>

      <Card>
        <div style={styles.row}>
          <div style={{ flex: 1 }}>
            <div style={styles.rowLabel}>Sign out</div>
            <div style={styles.rowValue}>End your current session on this device.</div>
          </div>
          <Button variant="danger" icon={LogOut} onClick={handleLogout}>
            Log out
          </Button>
        </div>
      </Card>
    </div>
  )
}

const styles = {
  row: { display: 'flex', alignItems: 'center', gap: 14 },
  rowIcon: { width: 34, height: 34, borderRadius: 9, background: 'var(--bg-surface-raised)', color: 'var(--accent)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 },
  rowLabel: { fontSize: 12, color: 'var(--text-tertiary)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.03em' },
  rowValue: { fontSize: 14, color: 'var(--text-primary)', fontWeight: 600, marginTop: 3 },
  note: { fontSize: 12.5, color: 'var(--text-tertiary)', marginTop: 14, paddingTop: 14, borderTop: '1px solid var(--border-subtle)', lineHeight: 1.5 },
}
