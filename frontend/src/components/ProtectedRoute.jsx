import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { Loader } from "@/components/Loader";

export const ProtectedRoute = ({ children }) => {
  const { user } = useAuth();
  const location = useLocation();
  if (user === null) return <Loader />;
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  return children;
};
