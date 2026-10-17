import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "@/components/ui/sonner";
import { AuthProvider } from "@/context/AuthContext";
import { Header } from "@/components/Header";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import Welcome from "@/pages/Welcome";
import Login from "@/pages/Login";
import Register from "@/pages/Register";
import Dashboard from "@/pages/Dashboard";
import Quiz from "@/pages/Quiz";
import Result from "@/pages/Result";
import MasterResults from "@/pages/MasterResults";
import AdminVerses from "@/pages/AdminVerses";
import { Footer } from "@/components/Footer";

const guard = (el) => <ProtectedRoute>{el}</ProtectedRoute>;

function App() {
  return (
    <div className="App flex min-h-screen flex-col bg-ink text-white">
      <BrowserRouter>
        <AuthProvider>
          <Header />
          <main className="flex-1">
            <Routes>
              <Route path="/" element={<Welcome />} />
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />
              <Route path="/welcome" element={guard(<Welcome firstVisit />)} />
              <Route path="/dashboard" element={guard(<Dashboard />)} />
              <Route path="/assessment/:id" element={guard(<Quiz />)} />
              <Route path="/assessment/:id/result" element={guard(<Result />)} />
              <Route path="/master-results" element={guard(<MasterResults />)} />
              <Route path="/admin/verses" element={guard(<AdminVerses />)} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </main>
          <Footer />
          <Toaster theme="dark" position="top-center" />
        </AuthProvider>
      </BrowserRouter>
    </div>
  );
}

export default App;
