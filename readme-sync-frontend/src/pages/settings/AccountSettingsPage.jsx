import {
  Mail,
  Github,
  LogOut,
} from 'lucide-react'

import {
  useAuth,
} from '../../context/AuthContext'

import {
  useNavigate,
  useSearchParams,
} from 'react-router-dom'

import {
  useEffect,
  useState,
} from 'react'

import {
  Card,
  Badge,
} from '../../components/ui/Primitives'

import Button from '../../components/ui/Button'

import {
  authApi,
} from '../../api/auth'


export default function AccountSettingsPage() {
  const {
    user,
    logout,
    refreshUser,
  } = useAuth()

  const navigate = useNavigate()

  const [
    searchParams,
    setSearchParams,
  ] = useSearchParams()

  const [
    isConnecting,
    setIsConnecting,
  ] = useState(false)

  const [
    githubError,
    setGithubError,
  ] = useState(null)


  // --------------------------------------------------------
  // Handle GitHub callback
  // --------------------------------------------------------

  useEffect(() => {
    const githubStatus =
      searchParams.get('github')

    if (githubStatus === 'connected') {
      refreshUser()
        .catch(() => {
          setGithubError(
            'GitHub connected, but the account could not be refreshed.'
          )
        })
        .finally(() => {
          const newParams =
            new URLSearchParams(searchParams)

          newParams.delete('github')

          setSearchParams(
            newParams,
            { replace: true }
          )
        })
    }

    if (githubStatus === 'error') {
      setGithubError(
        'GitHub connection was cancelled or failed.'
      )

      const newParams =
        new URLSearchParams(searchParams)

      newParams.delete('github')

      setSearchParams(
        newParams,
        { replace: true }
      )
    }
  }, [
    searchParams,
    setSearchParams,
    refreshUser,
  ])


  // --------------------------------------------------------
  // Connect GitHub
  // --------------------------------------------------------

  async function handleConnectGitHub() {
    setGithubError(null)
    setIsConnecting(true)

    try {
      const data =
        await authApi.githubAuthorize()

      if (!data?.authorization_url) {
        throw new Error(
          'GitHub authorization URL is missing.'
        )
      }

      window.location.href =
        data.authorization_url

    } catch (error) {
      setGithubError(
        error?.response?.data?.error ||
        error?.message ||
        'Unable to connect GitHub.'
      )

      setIsConnecting(false)
    }
  }


  // --------------------------------------------------------
  // Logout
  // --------------------------------------------------------

  function handleLogout() {
    logout()
    navigate('/login')
  }


  const isGithubConnected =
    Boolean(user?.github_username)


  return (
    <div style={{ maxWidth: 560 }}>

      {/* Email */}

      <Card style={{ marginBottom: 14 }}>
        <div style={styles.row}>

          <div style={styles.rowIcon}>
            <Mail size={16} />
          </div>

          <div
            style={{
              flex: 1,
              minWidth: 0,
            }}
          >
            <div style={styles.rowLabel}>
              Email
            </div>

            <div style={styles.rowValue}>
              {user?.email}
            </div>
          </div>

        </div>
      </Card>


      {/* GitHub */}

      <Card style={{ marginBottom: 14 }}>

        <div style={styles.row}>

          <div style={styles.rowIcon}>
            <Github size={16} />
          </div>

          <div
            style={{
              flex: 1,
              minWidth: 0,
            }}
          >

            <div style={styles.rowLabel}>
              GitHub
            </div>

            <div style={styles.rowValue}>
              {isGithubConnected
                ? `@${user.github_username}`
                : 'Not connected'}
            </div>

          </div>

          <Badge
            variant={
              isGithubConnected
                ? 'success'
                : 'neutral'
            }
            dot
          >
            {isGithubConnected
              ? 'Connected'
              : 'Not connected'}
          </Badge>

        </div>


        {/* Error */}

        {githubError && (
          <p style={styles.error}>
            {githubError}
          </p>
        )}


        {/* Not connected */}

        {!isGithubConnected && (
          <div style={styles.githubAction}>

            <p style={styles.note}>
              Connect your GitHub account to allow
              README Sync Platform to access your
              repositories and synchronize README
              changes.
            </p>

            <Button
              icon={Github}
              onClick={handleConnectGitHub}
              disabled={isConnecting}
            >
              {isConnecting
                ? 'Connecting...'
                : 'Connect GitHub'}
            </Button>

          </div>
        )}


        {/* Connected */}

        {isGithubConnected && (
          <p style={styles.noteConnected}>
            Your GitHub account is connected.
            You can now use GitHub repositories
            with README Sync Platform.
          </p>
        )}

      </Card>


      {/* Logout */}

      <Card>

        <div style={styles.row}>

          <div style={{ flex: 1 }}>

            <div style={styles.rowLabel}>
              Sign out
            </div>

            <div style={styles.rowValue}>
              End your current session on this device.
            </div>

          </div>

          <Button
            variant="danger"
            icon={LogOut}
            onClick={handleLogout}
          >
            Log out
          </Button>

        </div>

      </Card>

    </div>
  )
}


const styles = {

  row: {
    display: 'flex',
    alignItems: 'center',
    gap: 14,
  },

  rowIcon: {
    width: 34,
    height: 34,
    borderRadius: 9,
    background:
      'var(--bg-surface-raised)',
    color: 'var(--accent)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
  },

  rowLabel: {
    fontSize: 12,
    color: 'var(--text-tertiary)',
    fontWeight: 600,
    textTransform: 'uppercase',
    letterSpacing: '0.03em',
  },

  rowValue: {
    fontSize: 14,
    color: 'var(--text-primary)',
    fontWeight: 600,
    marginTop: 3,
  },

  githubAction: {
    marginTop: 14,
    paddingTop: 14,
    borderTop:
      '1px solid var(--border-subtle)',
  },

  note: {
    fontSize: 12.5,
    color: 'var(--text-tertiary)',
    marginTop: 0,
    marginBottom: 14,
    lineHeight: 1.5,
  },

  noteConnected: {
    fontSize: 12.5,
    color: 'var(--text-tertiary)',
    marginTop: 14,
    paddingTop: 14,
    borderTop:
      '1px solid var(--border-subtle)',
    lineHeight: 1.5,
  },

  error: {
    fontSize: 12.5,
    color: 'var(--danger)',
    marginTop: 14,
    lineHeight: 1.5,
  },

}