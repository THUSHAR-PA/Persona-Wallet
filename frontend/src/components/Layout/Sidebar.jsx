import { Link, useLocation, useNavigate } from "react-router-dom";
import {
  LayoutDashboard,
  Wallet,
  ArrowLeftRight,
  History,
  Brain,
  FileUp,
  LogOut,
} from "lucide-react";

function Sidebar() {
  const location = useLocation();
  const navigate = useNavigate();

  const menu = [
    { name: "Dashboard", path: "/", icon: <LayoutDashboard size={20} /> },
    { name: "Accounts", path: "/accounts", icon: <Wallet size={20} /> },
    { name: "Transfer", path: "/transfer", icon: <ArrowLeftRight size={20} /> },
    { name: "History", path: "/history", icon: <History size={20} /> },
    { name: "Financial Twin", path: "/profile", icon: <Brain size={20} /> },
    {
      name: "Bank Statements",
      path: "/statements",
      icon: <FileUp size={20} />,
    },
  ];

  return (
    <aside className="w-full shrink-0 bg-slate-900 p-5 text-white lg:min-h-screen lg:w-60 lg:p-6">
      <h1 className="text-2xl font-bold mb-8">Persona Wallet</h1>

      <nav className="flex flex-wrap gap-2 lg:flex-col">
        {menu.map((item) => (
          <Link
            key={item.path}
            to={item.path}
            className={`flex items-center gap-3 p-3 rounded-lg transition ${
              location.pathname === item.path
                ? "bg-blue-600"
                : "hover:bg-slate-800"
            }`}
          >
            {item.icon}
            {item.name}
          </Link>
        ))}
      </nav>
      <button
        className="mt-6 flex items-center gap-3 rounded-lg p-3 text-sm text-slate-300 hover:bg-slate-800"
        onClick={() => {
          localStorage.removeItem("access_token");
          navigate("/login");
        }}
      >
        <LogOut size={18} />
        Sign out
      </button>
    </aside>
  );
}

export default Sidebar;
