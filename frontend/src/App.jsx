import { Routes, Route } from "react-router-dom";

import Layout from "./components/Layout/Layout";

import Dashboard from "./pages/Dashboard";
import Accounts from "./pages/Accounts";
import Transfer from "./pages/Transfer";
import History from "./pages/Transactions";
import FinancialProfile from "./pages/FinancialProfile";

function App() {
  return (
    <Layout>
      <Routes>
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