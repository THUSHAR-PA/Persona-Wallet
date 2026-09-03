import { useEffect, useState } from "react";
import api from "../api";

function History() {
  const [transactions, setTransactions] = useState([]);
  const [currentUser, setCurrentUser] = useState(null);
  const [error, setError] = useState("");

  const fetchData = async () => {
    try {
      const [userResponse, transactionResponse] = await Promise.all([
        api.get("/auth/me"),
        api.get("/transactions/"),
      ]);

      setCurrentUser(userResponse.data);
      setTransactions(transactionResponse.data);
    } catch (error) {
      console.error("Failed to load transaction history:", error);

      setError(
        error.response?.data?.detail ||
        "Failed to load transaction history."
      );
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  return (
    <div className="max-w-4xl">

      <h1 className="text-4xl font-bold mb-2">
        Transaction History
      </h1>

      <p className="text-gray-500 mb-8">
        Your recent financial activity.
      </p>

      {error && (
        <div className="bg-red-100 text-red-700 p-4 rounded-lg mb-6">
          {error}
        </div>
      )}

      {transactions.length === 0 && !error && (
        <div className="bg-white rounded-xl shadow p-8 text-center text-gray-500">
          No transactions yet.
        </div>
      )}

      <div className="space-y-4">

        {transactions.map((transaction) => {

          const isSent =
            transaction.from_account.owner_username ===
            currentUser?.username;

          const otherUser = isSent
            ? transaction.to_account.owner_username
            : transaction.from_account.owner_username;

          const action = isSent
            ? "Sent to"
            : "Received from";

          return (
            <div
              key={transaction.id}
              className="bg-white rounded-xl shadow p-6"
            >

              <div className="flex justify-between items-start">

                <div>

                  <div className="flex items-center gap-3">

                    <h2 className="text-xl font-semibold">
                      ₹{Number(transaction.amount).toLocaleString("en-IN")}
                    </h2>

                    <span className="text-sm bg-green-100 text-green-700 px-2 py-1 rounded-full">
                      {transaction.status}
                    </span>

                  </div>

                  <p className="text-gray-600 mt-2">
                    {action}{" "}
                    <span className="font-semibold">
                      {otherUser}
                    </span>
                  </p>

                </div>

                <div className="text-sm text-gray-500">
                  #{transaction.id}
                </div>

              </div>

              <div className="mt-5 border-t pt-4 grid grid-cols-2 gap-4">

                <div>
                  <p className="text-sm text-gray-500">
                    From
                  </p>

                  <p className="font-medium">
                    {transaction.from_account.name}
                  </p>

                  <p className="text-sm text-gray-500">
                    @{transaction.from_account.owner_username}
                  </p>
                </div>

                <div>
                  <p className="text-sm text-gray-500">
                    To
                  </p>

                  <p className="font-medium">
                    {transaction.to_account.name}
                  </p>

                  <p className="text-sm text-gray-500">
                    @{transaction.to_account.owner_username}
                  </p>
                </div>

              </div>

              <div className="mt-4 flex justify-between text-sm text-gray-500">

                <span>
                  Category: {transaction.category}
                </span>

                {transaction.description && (
                  <span>
                    {transaction.description}
                  </span>
                )}

              </div>

            </div>
          );
        })}

      </div>

    </div>
  );
}

export default History;