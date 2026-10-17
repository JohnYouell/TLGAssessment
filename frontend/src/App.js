import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate, useLocation } from "react-router-dom";
import { useEffect } from "react";
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
import AdminSharing from "@/pages/AdminSharing";
import BookPage from "@/pages/BookPage";
import AdminEndorsements from "@/pages/AdminEndorsements";
import AdminPage from "@/pages/AdminPage";
import About from "@/pages/About";
import Contact from "@/pages/Contact";
import { Footer } from "@/components/Footer";
import { PaywallProvider } from "@/context/PaywallContext";
import { PaymentSuccess, PaymentCancel } from "@/pages/Payment";
import { ThankYou, InitialCongrats, SpreadTheWord, TrainingVideos } from "@/pages/VideoPages";
import AdminCodes from "@/pages/AdminCodes";
import AdminVideos from "@/pages/AdminVideos";

const guard = (el) => <ProtectedRoute>{el}</ProtectedRoute>;

const ScrollToTop = () => {
  const { pathname } = useLocation();
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [pathname]);
  return null;
};

function App() {
  return (
    <div className="App flex min-h-screen flex-col bg-ink text-white">
      <BrowserRouter>
        <AuthProvider>
          <PaywallProvider>
          <ScrollToTop />
          <Header />
          <main className="flex-1">
            <Routes>
              <Route path="/" element={<Welcome />} />
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />
              <Route path="/welcome" element={guard(<ThankYou />)} />
              <Route path="/congrats/initial" element={guard(<InitialCongrats />)} />
              <Route path="/spread-the-word" element={<SpreadTheWord />} />
              <Route path="/videos" element={guard(<TrainingVideos />)} />
              <Route path="/payment/success" element={guard(<PaymentSuccess />)} />
              <Route path="/payment/cancel" element={guard(<PaymentCancel />)} />
              <Route path="/admin/codes" element={guard(<AdminCodes />)} />
              <Route path="/admin/videos" element={guard(<AdminVideos />)} />
              <Route path="/dashboard" element={guard(<Dashboard />)} />
              <Route path="/assessment/:id" element={guard(<Quiz />)} />
              <Route path="/assessment/:id/result" element={guard(<Result />)} />
              <Route path="/master-results" element={guard(<MasterResults />)} />
              <Route path="/about" element={<About />} />
              <Route path="/book" element={<BookPage />} />
              <Route path="/contact" element={<Contact />} />
              <Route path="/admin/pages/:slug" element={guard(<AdminPage />)} />
              <Route path="/admin/verses" element={guard(<AdminVerses />)} />
              <Route path="/admin/sharing" element={guard(<AdminSharing />)} />
              <Route path="/admin/endorsements" element={guard(<AdminEndorsements />)} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </main>
          <Footer />
          <Toaster theme="dark" position="top-center" />
          </PaywallProvider>
        </AuthProvider>
      </BrowserRouter>
    </div>
  );
}

export default App;
