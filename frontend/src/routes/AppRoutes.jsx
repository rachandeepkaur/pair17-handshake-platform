import { Navigate, Route, Routes } from 'react-router-dom'
import CompanySignup from '../pages/auth/CompanySignup'
import Login from '../pages/auth/Login'
import StudentLogin from '../pages/auth/StudentLogin'
import StudentSignup from '../pages/auth/StudentSignup'
import AcceptInvite from '../pages/auth/AcceptInvite'
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
import CompanyStudentProfile from '../pages/company/StudentProfile'
import Analytics from '../pages/company/Analytics'
import CompanyProfile from '../pages/company/CompanyProfile'
import Messages from '../pages/company/Messages'
import Team from '../pages/company/Team'
import Settings from '../pages/company/Settings'
import StudentLayout from '../components/layout/StudentLayout'
import StudentDashboard from '../pages/student/Dashboard'
import StudentProfile from '../pages/student/Profile'
import StudentJobs from '../pages/student/Jobs'
import StudentJobDetail from '../pages/student/JobDetail'
import MyApplications from '../pages/student/MyApplications'
import StudentEvents from '../pages/student/Events'
import StudentEventDetail from '../pages/student/EventDetail'
import RegisteredEvents from '../pages/student/RegisteredEvents'
import People from '../pages/student/People'
import NotFound from '../pages/NotFound'
import ProtectedRoute from './ProtectedRoute'

export default function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/signup/company" element={<CompanySignup />} />
      <Route path="/student/login" element={<StudentLogin />} />
      <Route path="/signup/student" element={<StudentSignup />} />
      <Route path="/invite/:token" element={<AcceptInvite />} />

      <Route path="/student" element={<ProtectedRoute role="student"><StudentLayout /></ProtectedRoute>}>
        <Route index element={<Navigate to="dashboard" replace />} />
        <Route path="dashboard" element={<StudentDashboard />} />
        <Route path="profile" element={<StudentProfile />} />
        <Route path="jobs" element={<StudentJobs />} />
        <Route path="jobs/:jobId" element={<StudentJobDetail />} />
        <Route path="applications" element={<MyApplications />} />
        <Route path="events" element={<StudentEvents />} />
        <Route path="events/registrations" element={<RegisteredEvents />} />
        <Route path="events/:eventId" element={<StudentEventDetail />} />
        <Route path="people" element={<People />} />
      </Route>

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
        <Route path="students/:studentId" element={<CompanyStudentProfile />} />
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
