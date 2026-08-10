import { Routes, Route, Navigate } from 'react-router-dom'
import ProtectedRoute from '../components/ProtectedRoute'
import AuthLayout from '../layouts/AuthLayout'
import MainLayout from '../layouts/MainLayout'

import Login from '../pages/auth/Login'
import Register from '../pages/auth/Register'
import ForgotPassword from '../pages/auth/ForgotPassword'

import Dashboard from '../pages/Dashboard'
import Repositories from '../pages/Repositories'
import AddRepository from '../pages/AddRepository'
import RepositoryDetails from '../pages/RepositoryDetails'
import RepositorySettings from '../pages/RepositorySettings'
import Scans from '../pages/Scans'
import ScanDetails from '../pages/ScanDetails'
import PendingUpdates from '../pages/PendingUpdates'
import PendingUpdateDetails from '../pages/PendingUpdateDetails'
import NotFound from '../pages/NotFound'

export default function AppRoutes() {
  return (
    <Routes>
      {/* Racine : renvoie vers /login (ou /dashboard si déjà connecté, géré par ProtectedRoute) */}
      <Route path="/" element={<Navigate to="/login" replace />} />

      {/* Auth */}
      <Route element={<AuthLayout />}>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/forgot-password" element={<ForgotPassword />} />
      </Route>

      {/* App protégée */}
      <Route element={<ProtectedRoute />}>
        <Route element={<MainLayout />}>
          <Route path="/dashboard" element={<Dashboard />} />

          <Route path="/repositories" element={<Repositories />} />
          <Route path="/repositories/add" element={<AddRepository />} />
          <Route path="/repositories/:id" element={<RepositoryDetails />} />
          <Route path="/repositories/:id/settings" element={<RepositorySettings />} />

          <Route path="/scans" element={<Scans />} />
          <Route path="/scans/:id" element={<ScanDetails />} />

          <Route path="/pending-updates" element={<PendingUpdates />} />
          <Route path="/pending-updates/:id" element={<PendingUpdateDetails />} />
        </Route>
      </Route>

      <Route path="*" element={<NotFound />} />
    </Routes>
  )
}
