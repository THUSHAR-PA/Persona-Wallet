import { useEffect, useState } from "react";
import api from "../api";

function Transfer() {
  const [accounts, setAccounts] = useState([]);

  const [fromAccount, setFromAccount] = useState("");
  const [toAccount, setToAccount] = useState("");
  const [amount, setAmount] = useState("");
  const [category, setCategory] = useState("TRANSFER");
  const [description, setDescription] = useState("");

  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const fetchAccounts = async () => {
    try {
      const response = await api.get("/accounts/");
      setAccounts(response.data);
    } catch (error) {
      console.error("Failed to load accounts:", error);
      setError("Failed to load accounts.");
    }
  };

  useEffect(() => {
    fetchAccounts();
  }, []);

  const handleTransfer = async (e) => {
    e.preventDefault();

    setMessage("");
    setError("");

    if (!fromAccount || !toAccount) {
      setError("Please select both accounts.");
      return;
    }

    if (fromAccount === toAccount) {
      setError("Source and destination must be different.");
      return;
    }

    if (!amount || Number(amount) <= 0) {
      setError("Enter a valid amount.");
      return;
    }

    try {
      await api.post("/transactions/", {
        from_account_id: Number(fromAccount),
        to_account_id: Number(toAccount),
        amount: Number(amount),
        category: category,
        description: description || null,
      });

      setMessage("Transaction completed successfully.");

      setFromAccount("");
      setToAccount("");
      setAmount("");
      setCategory("TRANSFER");
      setDescription("");

      await fetchAccounts();

    } catch (error) {
      console.error("Transaction failed:", error);

      setError(
        error.response?.data?.detail ||
        "Transaction failed."
      );
    }
  };

  return (
    <div className="max-w-2xl">

      <h1 className="text-4xl font-bold mb-2">
        Transfer Money
      </h1>

      <p className="text-gray-500 mb-8">
        Send money between your accounts and financial entities.
      </p>

      <form
        onSubmit={handleTransfer}
        className="bg-white rounded-xl shadow p-8 space-y-6"
      >

        {/* From */}
        <div>
          <label className="block font-medium mb-2">
            From Account
          </label>

          <select
            value={fromAccount}
            onChange={(e) => setFromAccount(e.target.value)}
            className="w-full border rounded-lg p-3"
          >
            <option value="">
              Select source account
            </option>

            {accounts.map((account) => (
              <option
                key={account.id}
                value={account.id}
              >
                {account.name} — {account.account_type} — ₹
                {Number(account.balance).toLocaleString("en-IN")}
              </option>
            ))}
          </select>
        </div>

        {/* To */}
        <div>
          <label className="block font-medium mb-2">
            To Account
          </label>

          <select
            value={toAccount}
            onChange={(e) => setToAccount(e.target.value)}
            className="w-full border rounded-lg p-3"
          >
            <option value="">
              Select destination
            </option>

            {accounts.map((account) => (
              <option
                key={account.id}
                value={account.id}
              >
                {account.name} — {account.account_type}
              </option>
            ))}
          </select>
        </div>

        {/* Category */}
        <div>
          <label className="block font-medium mb-2">
            Transaction Type
          </label>

          <select
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            className="w-full border rounded-lg p-3"
          >
            <option value="TRANSFER">Transfer</option>
            <option value="PURCHASE">Purchase</option>
            <option value="RENT">Rent</option>
            <option value="INVESTMENT">Investment</option>
            <option value="SUBSCRIPTION">Subscription</option>
            <option value="TAX">Tax</option>
            <option value="OTHER">Other</option>
          </select>
        </div>

        {/* Amount */}
        <div>
          <label className="block font-medium mb-2">
            Amount
          </label>

          <input
            type="number"
            min="0"
            step="0.01"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            placeholder="Enter amount"
            className="w-full border rounded-lg p-3"
          />
        </div>

        {/* Description */}
        <div>
          <label className="block font-medium mb-2">
            Description
          </label>

          <input
            type="text"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="e.g. Monthly rent"
            className="w-full border rounded-lg p-3"
          />
        </div>

        {/* Messages */}
        {message && (
          <div className="bg-green-100 text-green-700 p-3 rounded-lg">
            {message}
          </div>
        )}

        {error && (
          <div className="bg-red-100 text-red-700 p-3 rounded-lg">
            {error}
          </div>
        )}

        <button
          type="submit"
          className="w-full bg-blue-600 text-white p-3 rounded-lg font-semibold hover:bg-blue-700"
        >
          Complete Transaction
        </button>

      </form>
    </div>
  );
}

export default Transfer;