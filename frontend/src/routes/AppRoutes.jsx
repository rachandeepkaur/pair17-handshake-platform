import { Route, Routes } from 'react-router-dom'
import CompanySignup from '../pages/auth/CompanySignup'
import Login from '../pages/auth/Login'
import CompanyDashboard from '../pages/company/Dashboard'
import MyJobs from '../pages/company/MyJobs'
import PostJob from '../pages/company/PostJob'
import NotFound from '../pages/NotFound'
import ProtectedRoute from './ProtectedRoute'

export default function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/signup/company" element={<CompanySignup />} />
      <Route
        path="/company/dashboard"
        element={
          <ProtectedRoute role="company">
            <CompanyDashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/company/jobs"
        element={
          <ProtectedRoute role="company">
            <MyJobs />
          </ProtectedRoute>
        }
      />
      <Route
        path="/company/jobs/new"
        element={
          <ProtectedRoute role="company">
            <PostJob />
          </ProtectedRoute>
        }
      />
      <Route path="*" element={<NotFound />} />
    </Routes>
  )
}
