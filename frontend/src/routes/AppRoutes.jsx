import { Navigate, Route, Routes } from 'react-router-dom'
import CompanySignup from '../pages/auth/CompanySignup'
import Login from '../pages/auth/Login'
import CompanyLayout from '../components/layout/CompanyLayout'
import CompanyDashboard from '../pages/company/Dashboard'
import MyJobs from '../pages/company/MyJobs'
import PostJob from '../pages/company/PostJob'
import JobDetail from '../pages/company/JobDetail'
import Applicants from '../pages/company/Applicants'
import ApplicantProfile from '../pages/company/ApplicantProfile'
import CompanyEvents from '../pages/company/CompanyEvents'
import CreateEvent from '../pages/company/CreateEvent'
import EventRegistrations from '../pages/company/EventRegistrations'
import StudentSearch from '../pages/company/StudentSearch'
import StudentProfile from '../pages/company/StudentProfile'
import Analytics from '../pages/company/Analytics'
import CompanyProfile from '../pages/company/CompanyProfile'
import Messages from '../pages/company/Messages'
import Team from '../pages/company/Team'
import Settings from '../pages/company/Settings'
import NotFound from '../pages/NotFound'
import ProtectedRoute from './ProtectedRoute'

export default function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/signup/company" element={<CompanySignup />} />

      <Route
        path="/company"
        element={
          <ProtectedRoute role="company">
            <CompanyLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="/company/dashboard" replace />} />
        <Route path="dashboard" element={<CompanyDashboard />} />
        <Route path="jobs" element={<MyJobs />} />
        <Route path="jobs/new" element={<PostJob />} />
        <Route path="jobs/:jobId" element={<JobDetail />} />
        <Route path="applicants" element={<Applicants />} />
        <Route path="applications/:applicationId" element={<ApplicantProfile />} />
        <Route path="events" element={<CompanyEvents />} />
        <Route path="events/new" element={<CreateEvent />} />
        <Route path="events/:eventId" element={<EventRegistrations />} />
        <Route path="students" element={<StudentSearch />} />
        <Route path="students/:studentId" element={<StudentProfile />} />
        <Route path="analytics" element={<Analytics />} />
        <Route path="profile" element={<CompanyProfile />} />
        <Route path="messages" element={<Messages />} />
        <Route path="team" element={<Team />} />
        <Route path="settings" element={<Settings />} />
        <Route path="*" element={<NotFound />} />
      </Route>

      <Route path="/" element={<Navigate to="/login" replace />} />
      <Route path="*" element={<NotFound />} />
    </Routes>
  )
}
