import { Link, useLocation } from "react-router-dom";
import {
  LayoutDashboard,
  Wallet,
  ArrowLeftRight,
  History,
  Brain,
} from "lucide-react";

function Sidebar() {
  const location = useLocation();

  const menu = [
    { name: "Dashboard", path: "/", icon: <LayoutDashboard size={20} /> },
    { name: "Accounts", path: "/accounts", icon: <Wallet size={20} /> },
    { name: "Transfer", path: "/transfer", icon: <ArrowLeftRight size={20} /> },
    { name: "History", path: "/history", icon: <History size={20} /> },
    { name: "Financial Twin", path: "/profile", icon: <Brain size={20} /> },
  ];

  return (
    <div className="w-64 bg-slate-900 text-white min-h-screen p-6">
      <h1 className="text-2xl font-bold mb-8">Persona Wallet</h1>

      <div className="space-y-2">
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
      </div>
    </div>
  );
}

export default Sidebar;