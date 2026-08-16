import { useEffect, useState } from "react";
import axios from "axios";

function Accounts() {
  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchAccounts = async () => {
    try {
      const response = await axios.get(
        "http://127.0.0.1:8000/accounts/"
      );

      setAccounts(response.data);
    } catch (error) {
      console.error("Failed to fetch accounts:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAccounts();
  }, []);

  if (loading) {
    return <p>Loading accounts...</p>;
  }

  return (
    <div>
      <h1 className="text-4xl font-bold mb-8">
        My Accounts
      </h1>

      {accounts.length === 0 ? (
        <p className="text-gray-500">
          No accounts found.
        </p>
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