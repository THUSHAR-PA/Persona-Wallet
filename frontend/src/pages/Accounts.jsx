import { useEffect, useState } from "react";
import api from "../api";

function Accounts() {
  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(true);

  const [showForm, setShowForm] = useState(false);

  const [name, setName] = useState("");
  const [accountType, setAccountType] = useState("PERSONAL");
  const [balance, setBalance] = useState("");
  const [currency, setCurrency] = useState("INR");

  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const fetchAccounts = async () => {
    try {
      const response = await api.get("/accounts/");
      setAccounts(response.data);
    } catch (error) {
      console.error("Failed to fetch accounts:", error);
      setError("Failed to load accounts.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAccounts();
  }, []);

  const handleCreateAccount = async (e) => {
    e.preventDefault();

    setMessage("");
    setError("");

    if (!name.trim()) {
      setError("Account name is required.");
      return;
    }

    if (balance === "" || Number(balance) < 0) {
      setError("Enter a valid balance.");
      return;
    }

    try {
      await api.post("/accounts/", {
        name: name.trim(),
        account_type: accountType,
        balance: Number(balance),
        currency,
      });

      setMessage("Account created successfully.");

      setName("");
      setAccountType("PERSONAL");
      setBalance("");
      setCurrency("INR");

      setShowForm(false);

      await fetchAccounts();
    } catch (error) {
      console.error("Failed to create account:", error);

      setError(
        error.response?.data?.detail ||
        "Failed to create account."
      );
    }
  };

  if (loading) {
    return <p>Loading accounts...</p>;
  }

  return (
    <div>

      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-4xl font-bold">
            My Accounts
          </h1>

          <p className="text-gray-500 mt-2">
            Manage your financial accounts and entities.
          </p>
        </div>

        <button
          onClick={() => {
            setShowForm(!showForm);
            setError("");
            setMessage("");
          }}
          className="bg-blue-600 text-white px-5 py-3 rounded-lg font-semibold hover:bg-blue-700"
        >
          {showForm ? "Cancel" : "+ Add Account"}
        </button>
      </div>

      {/* Messages */}
      {message && (
        <div className="bg-green-100 text-green-700 p-3 rounded-lg mb-6">
          {message}
        </div>
      )}

      {error && (
        <div className="bg-red-100 text-red-700 p-3 rounded-lg mb-6">
          {error}
        </div>
      )}

      {/* Create Account Form */}
      {showForm && (
        <form
          onSubmit={handleCreateAccount}
          className="bg-white rounded-xl shadow p-6 mb-8 max-w-2xl"
        >
          <h2 className="text-2xl font-semibold mb-6">
            Create Account
          </h2>

          {/* Name */}
          <div className="mb-5">
            <label className="block font-medium mb-2">
              Account Name
            </label>

            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. HDFC Main Account"
              className="w-full border rounded-lg p-3"
            />
          </div>

          {/* Type */}
          <div className="mb-5">
            <label className="block font-medium mb-2">
              Account Type
            </label>

            <select
              value={accountType}
              onChange={(e) => setAccountType(e.target.value)}
              className="w-full border rounded-lg p-3"
            >
              <option value="PERSONAL">Personal</option>
              <option value="EMPLOYER">Employer</option>
              <option value="MERCHANT">Merchant</option>
              <option value="LANDLORD">Landlord</option>
              <option value="INVESTMENT">Investment</option>
              <option value="SUBSCRIPTION">Subscription</option>
              <option value="GOVERNMENT">Government</option>
            </select>
          </div>

          {/* Balance */}
          <div className="mb-5">
            <label className="block font-medium mb-2">
              Initial Balance
            </label>

            <input
              type="number"
              min="0"
              step="0.01"
              value={balance}
              onChange={(e) => setBalance(e.target.value)}
              placeholder="0"
              className="w-full border rounded-lg p-3"
            />
          </div>

          {/* Currency */}
          <div className="mb-6">
            <label className="block font-medium mb-2">
              Currency
            </label>

            <select
              value={currency}
              onChange={(e) => setCurrency(e.target.value)}
              className="w-full border rounded-lg p-3"
            >
              <option value="INR">INR</option>
              <option value="USD">USD</option>
              <option value="AED">AED</option>
            </select>
          </div>

          <button
            type="submit"
            className="bg-blue-600 text-white px-5 py-3 rounded-lg font-semibold hover:bg-blue-700"
          >
            Create Account
          </button>
        </form>
      )}

      {/* Accounts */}
      {accounts.length === 0 ? (
        <div className="bg-white rounded-xl shadow p-8 text-center">
          <p className="text-gray-500">
            You don't have any accounts yet.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">

          {accounts.map((account) => (
            <div
              key={account.id}
              className="bg-white rounded-xl shadow p-6"
            >
              <p className="text-sm text-gray-500">
                {account.account_type}
              </p>

              <h2 className="text-xl font-semibold mt-2">
                {account.name}
              </h2>

              <p className="text-3xl font-bold mt-4">
                ₹{Number(account.balance).toLocaleString("en-IN")}
              </p>

              <p className="text-sm text-gray-500 mt-2">
                {account.currency}
              </p>
            </div>
          ))}

        </div>
      )}

    </div>
  );
}

export default Accounts;