import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';
import Sidebar from './components/Sidebar';
import Navbar from './components/Navbar';
import AICoach from './components/AICoach';

// Auth
import LoginPage from './pages/LoginPage';
import OnboardingPage from './pages/OnboardingPage';
import AccessRestrictedPage from './pages/AccessRestrictedPage';

// Student
import StudentDashboard from './pages/StudentDashboard';
import MyLearningPage from './pages/MyLearningPage';
import CoursesPage from './pages/CoursesPage';
import VideoListPage from './pages/VideoListPage';
import VideoPlayerPage from './pages/VideoPlayerPage';
import QuizListPage from './pages/QuizListPage';
import QuizPage from './pages/QuizPage';
import QuizResultPage from './pages/QuizResultPage';
import PredictionPage from './pages/PredictionPage';
import ExplanationPage from './pages/ExplanationPage';
import RecommendationsPage from './pages/RecommendationsPage';
import EarlyWarningPage from './pages/EarlyWarningPage';
import ProgressPage from './pages/ProgressPage';
import AchievementsPage from './pages/AchievementsPage';
import StudentProfilePage from './pages/StudentProfilePage';
import CourseDetailPage from './pages/CourseDetailPage';

// Teacher
import TeacherDashboard from './pages/TeacherDashboard';
import TeacherAIInsightsPage from './pages/TeacherAIInsightsPage';
import TeacherCoursesPage from './pages/TeacherCoursesPage';

// Admin
import AdminDashboard from './pages/AdminDashboard';

const ProtectedLayout = ({ children, allowedRoles }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return <div style={{ padding: '40px', color: 'var(--text-muted)' }}>Loading EngageAI...</div>;
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return <Navigate to="/access-restricted" replace />;
  }

  // CORRECTION 1: Onboarding gate — only for students with no profile
  const onboardingDone = localStorage.getItem('engageai_onboarding_done') === 'true';
  const hasProfile = user.profile && user.profile.gender;
  if (user.role === 'student' && !onboardingDone && !hasProfile) {
    return <Navigate to="/onboarding" replace />;
  }

  return (
    <div style={{ display: 'flex', minHeight: '100vh', backgroundColor: 'var(--bg-dark)' }}>
      <Sidebar />
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <Navbar />
        <main style={{ flex: 1, padding: '28px' }}>
          {children}
        </main>
      </div>
      {/* Floating AI Coach — only for students */}
      {user.role === 'student' && <AICoach />}
    </div>
  );
};

function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <BrowserRouter>
        <Routes>
          {/* Public Routes */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/onboarding" element={<OnboardingPage />} />
          <Route path="/access-restricted" element={<AccessRestrictedPage />} />

          {/* ── Student Routes ─────────────────────────────────────────────── */}
          <Route path="/dashboard" element={
            <ProtectedLayout allowedRoles={['student', 'teacher', 'admin']}>
              <StudentDashboard />
            </ProtectedLayout>
          } />
          <Route path="/my-learning" element={
            <ProtectedLayout allowedRoles={['student']}>
              <MyLearningPage />
            </ProtectedLayout>
          } />
          <Route path="/courses" element={
            <ProtectedLayout allowedRoles={['student', 'teacher', 'admin']}>
              <CoursesPage />
            </ProtectedLayout>
          } />
          <Route path="/courses/:id" element={
            <ProtectedLayout allowedRoles={['student', 'teacher', 'admin']}>
              <CourseDetailPage />
            </ProtectedLayout>
          } />
          <Route path="/videos" element={
            <ProtectedLayout allowedRoles={['student', 'teacher', 'admin']}>
              <VideoListPage />
            </ProtectedLayout>
          } />
          <Route path="/videos/:id" element={
            <ProtectedLayout allowedRoles={['student', 'teacher', 'admin']}>
              <VideoPlayerPage />
            </ProtectedLayout>
          } />
          <Route path="/quizzes" element={
            <ProtectedLayout allowedRoles={['student', 'teacher', 'admin']}>
              <QuizListPage />
            </ProtectedLayout>
          } />
          <Route path="/quizzes/:id" element={
            <ProtectedLayout allowedRoles={['student', 'teacher', 'admin']}>
              <QuizPage />
            </ProtectedLayout>
          } />
          <Route path="/quizzes/:id/result" element={
            <ProtectedLayout allowedRoles={['student', 'teacher', 'admin']}>
              <QuizResultPage />
            </ProtectedLayout>
          } />
          <Route path="/prediction" element={
            <ProtectedLayout allowedRoles={['student', 'teacher', 'admin']}>
              <PredictionPage />
            </ProtectedLayout>
          } />
          <Route path="/explanation" element={
            <ProtectedLayout allowedRoles={['student', 'teacher', 'admin']}>
              <ExplanationPage />
            </ProtectedLayout>
          } />
          <Route path="/recommendations" element={
            <ProtectedLayout allowedRoles={['student', 'teacher', 'admin']}>
              <RecommendationsPage />
            </ProtectedLayout>
          } />
          <Route path="/early-warning" element={
            <ProtectedLayout allowedRoles={['student', 'teacher', 'admin']}>
              <EarlyWarningPage />
            </ProtectedLayout>
          } />
          <Route path="/progress" element={
            <ProtectedLayout allowedRoles={['student']}>
              <ProgressPage />
            </ProtectedLayout>
          } />
          <Route path="/achievements" element={
            <ProtectedLayout allowedRoles={['student']}>
              <AchievementsPage />
            </ProtectedLayout>
          } />
          <Route path="/profile" element={
            <ProtectedLayout allowedRoles={['student']}>
              <StudentProfilePage />
            </ProtectedLayout>
          } />

          {/* ── Teacher Routes ─────────────────────────────────────────────── */}
          <Route path="/teacher/dashboard" element={
            <ProtectedLayout allowedRoles={['teacher', 'admin']}>
              <TeacherDashboard />
            </ProtectedLayout>
          } />
          <Route path="/teacher/at-risk" element={
            <ProtectedLayout allowedRoles={['teacher', 'admin']}>
              <TeacherDashboard />
            </ProtectedLayout>
          } />
          <Route path="/teacher/ai-insights" element={
            <ProtectedLayout allowedRoles={['teacher', 'admin']}>
              <TeacherAIInsightsPage />
            </ProtectedLayout>
          } />
          <Route path="/teacher/content" element={
            <ProtectedLayout allowedRoles={['teacher', 'admin']}>
              <TeacherCoursesPage />
            </ProtectedLayout>
          } />
          <Route path="/teacher/quizzes" element={
            <ProtectedLayout allowedRoles={['teacher', 'admin']}>
              <QuizListPage />
            </ProtectedLayout>
          } />

          {/* ── Admin Routes ───────────────────────────────────────────────── */}
          <Route path="/admin/dashboard" element={
            <ProtectedLayout allowedRoles={['admin']}>
              <AdminDashboard />
            </ProtectedLayout>
          } />

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </BrowserRouter>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
