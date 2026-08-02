function Dashboard() {
  const stats = [
    {
      title: "Balance",
      value: "₹48,500",
    },
    {
      title: "Income",
      value: "₹50,000",
    },
    {
      title: "Expenses",
      value: "₹18,000",
    },
    {
      title: "Health Score",
      value: "82 / 100",
    },
  ];

  return (
    <div>
      <h1 className="text-4xl font-bold mb-8">
        Financial Command Center
      </h1>

      <div className="grid grid-cols-4 gap-6">
        {stats.map((card) => (
          <div
            key={card.title}
            className="bg-white rounded-xl shadow p-6"
          >
            <p className="text-gray-500">{card.title}</p>

            <h2 className="text-3xl font-bold mt-2">
              {card.value}
            </h2>
          </div>
        ))}
      </div>

      <div className="bg-white rounded-xl shadow mt-10 p-6">
        <h2 className="text-2xl font-semibold mb-4">
          Recent Transactions
        </h2>

        <div className="space-y-4">
          <div className="flex justify-between">
            <span>Salary</span>
            <span className="text-green-600">+ ₹50,000</span>
          </div>

          <div className="flex justify-between">
            <span>Swiggy</span>
            <span className="text-red-600">- ₹250</span>
          </div>

          <div className="flex justify-between">
            <span>Netflix</span>
            <span className="text-red-600">- ₹499</span>
          </div>

          <div className="flex justify-between">
            <span>Amazon Refund</span>
            <span className="text-green-600">+ ₹1,200</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;