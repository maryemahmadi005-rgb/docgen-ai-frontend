import { Routes, Route } from 'react-router-dom'

import ProtectedRoute, { GuestRoute } from './components/ProtectedRoute'
import AppShell from './components/layout/AppShell'
import RootEntry from './components/RootEntry'

import LoginPage from './pages/auth/LoginPage'
import RegisterPage from './pages/auth/RegisterPage'
import DashboardPage from './pages/dashboard/DashboardPage'

import RepositoriesListPage from './pages/repositories/RepositoriesListPage'
import AddRepositoryPage from './pages/repositories/AddRepositoryPage'
import RepositoryLayout from './pages/repositories/RepositoryLayout'
import RepositoryOverviewPage from './pages/repositories/RepositoryOverviewPage'
import RepositoryAnalysisPage from './pages/repositories/RepositoryAnalysisPage'
import RepositorySettingsPage from './pages/repositories/RepositorySettingsPage'

import ReadmeEditorPage from './pages/readme/ReadmeEditorPage'
import ReadmeVersionsPage from './pages/readme/ReadmeVersionsPage'
import ReadmeVersionDetailPage from './pages/readme/ReadmeVersionDetailPage'

import PendingUpdatesListPage from './pages/pending/PendingUpdatesListPage'
import PendingUpdateDetailPage from './pages/pending/PendingUpdateDetailPage'
import GlobalPendingUpdatesPage from './pages/pending/GlobalPendingUpdatesPage'

import AccountSettingsPage from './pages/settings/AccountSettingsPage'
import NotFoundPage from './pages/errors/NotFoundPage'

export default function App() {
  return (
    <Routes>
      {/* Public */}
      <Route path="/" element={<RootEntry />} />
      <Route path="/login" element={<GuestRoute><LoginPage /></GuestRoute>} />
      <Route path="/register" element={<GuestRoute><RegisterPage /></GuestRoute>} />

      {/* Authenticated app shell */}
      <Route
        element={
          <ProtectedRoute>
            <AppShell />
          </ProtectedRoute>
        }
      >
        <Route path="/dashboard" element={<DashboardPage />} />

        <Route path="/repositories" element={<RepositoriesListPage />} />
        <Route path="/repositories/new" element={<AddRepositoryPage />} />

        <Route path="/repositories/:repoId" element={<RepositoryLayout />}>
          <Route index element={<RepositoryOverviewPage />} />
          <Route path="readme" element={<ReadmeEditorPage />} />
          <Route path="analysis" element={<RepositoryAnalysisPage />} />
          <Route path="versions" element={<ReadmeVersionsPage />} />
          <Route path="versions/:versionNumber" element={<ReadmeVersionDetailPage />} />
          <Route path="pending-updates" element={<PendingUpdatesListPage />} />
          <Route path="pending-updates/:updateId" element={<PendingUpdateDetailPage />} />
          <Route path="settings" element={<RepositorySettingsPage />} />
        </Route>

        <Route path="/pending-updates" element={<GlobalPendingUpdatesPage />} />
        <Route path="/settings" element={<AccountSettingsPage />} />
      </Route>

      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}
