import { Navigate, useLocation } from "react-router-dom";
import Sidebar from "./Sidebar";

function Layout({ children }) {
  const location = useLocation();
  const isAuthPage = location.pathname === "/login";

  if (isAuthPage) {
    return <>{children}</>;
  }
  if (!localStorage.getItem("access_token"))
    return <Navigate to="/login" replace />;

  return (
    <div className="min-h-screen bg-slate-50 lg:flex">
      <Sidebar />
      <main className="min-w-0 flex-1 p-5 sm:p-8 lg:p-10">{children}</main>
    </div>
  );
}

export default Layout;
