import { Navigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { Loader } from "@/components/Loader";

export const ProtectedRoute = ({ children }) => {
  const { user } = useAuth();
  if (user === null) return <Loader />;
  if (!user) return <Navigate to="/login" replace />;
  return children;
};
