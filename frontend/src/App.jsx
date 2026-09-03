import { Routes, Route } from "react-router-dom";
import History from "./pages/History";
import Layout from "./components/Layout/Layout";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Accounts from "./pages/Accounts";
import Transfer from "./pages/Transfer";

import FinancialProfile from "./pages/FinancialProfile";

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={<Dashboard />} />
        <Route path="/accounts" element={<Accounts />} />
        <Route path="/transfer" element={<Transfer />} />
        <Route path="/history" element={<History />} />
        <Route path="/profile" element={<FinancialProfile />} />
        
      </Routes>
    </Layout>
  );
}

export default App;