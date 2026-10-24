import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./auth/AuthContext";
import { Navbar } from "./components/Navbar";
import AdminPage from "./pages/AdminPage";
import AuthPage from "./pages/AuthPage";
import InventoryPage from "./pages/InventoryPage";
import OrdersPage from "./pages/OrdersPage";

export default function App() {
  const { user, loading } = useAuth();
  if (loading) return <p className="p-10 text-center text-muted">Starting up…</p>;
  if (!user) return <AuthPage />;

  return (
    <>
      <Navbar />
      <Routes>
        <Route path="/" element={<InventoryPage />} />
        <Route path="/orders" element={<OrdersPage />} />
        <Route path="/admin" element={user.role === "admin" ? <AdminPage /> : <Navigate to="/" replace />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </>
  );
}
