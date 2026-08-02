import Sidebar from "./Sidebar";

function Layout({ children }) {
  return (
    <div className="flex bg-slate-100 min-h-screen">
      <Sidebar />

      <main className="flex-1 p-8">{children}</main>
    </div>
  );
}

export default Layout;