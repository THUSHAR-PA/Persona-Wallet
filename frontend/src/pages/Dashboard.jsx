import { useEffect, useMemo, useState } from "react";
import { ArrowDownLeft, ArrowUpRight, Landmark, PiggyBank, WalletCards } from "lucide-react";
import api from "../api";

const money = (value) =>
  new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(Number(value || 0));

function Dashboard() {
  const [summary, setSummary] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .get("/integration/financial-summary")
      .then((response) => setSummary(response.data))
      .catch((err) =>
        setError(err.response?.data?.detail || "Failed to load wallet overview.")
      );
  }, []);

  const stats = useMemo(() => {
    const metrics = summary?.metrics || {};
    return [
      { title: "Total balance", value: money(metrics.total_balance), icon: WalletCards },
      { title: "Money in", value: money(metrics.total_inflow), icon: ArrowDownLeft },
      { title: "Money out", value: money(metrics.total_outflow), icon: ArrowUpRight },
      {
        title: "Savings rate",
        value: `${Number(metrics.savings_rate_percent || 0).toFixed(1)}%`,
        icon: PiggyBank,
      },
    ];
  }, [summary]);

  if (error) {
    return <div className="rounded-2xl bg-red-50 p-5 text-red-700">{error}</div>;
  }

  if (!summary) {
    return <div className="text-slate-500">Loading your financial twin...</div>;
  }

  return (
    <div className="mx-auto max-w-7xl">
      <div className="mb-8 flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.18em] text-blue-600">
            Persona Wallet
          </p>
          <h1 className="mt-2 text-4xl font-bold tracking-tight text-slate-950">
            Your financial command center
          </h1>
          <p className="mt-2 text-slate-500">
            Live wallet data for @{summary.user.username}, shaped for your PersonaTwin.
          </p>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-600 shadow-sm">
          {summary.accounts.length} connected account{summary.accounts.length === 1 ? "" : "s"}
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {stats.map(({ title, value, icon: Icon }) => (
          <div key={title} className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex items-center justify-between">
              <p className="text-sm font-medium text-slate-500">{title}</p>
              <div className="rounded-2xl bg-slate-100 p-2.5 text-slate-700">
                <Icon size={18} />
              </div>
            </div>
            <p className="mt-5 text-3xl font-bold tracking-tight text-slate-950">{value}</p>
          </div>
        ))}
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-[1.4fr_0.8fr]">
        <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="mb-5 flex items-center justify-between">
            <div>
              <h2 className="text-xl font-semibold text-slate-950">Recent activity</h2>
              <p className="text-sm text-slate-500">Latest money movement across your wallet.</p>
            </div>
            <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">
              {summary.metrics.transaction_count} total
            </span>
          </div>

          <div className="divide-y divide-slate-100">
            {summary.recent_transactions.length === 0 ? (
              <p className="py-8 text-sm text-slate-500">No transactions yet.</p>
            ) : (
              summary.recent_transactions.map((transaction) => {
                const incoming = transaction.direction === "INFLOW";
                return (
                  <div key={transaction.id} className="flex items-center justify-between gap-4 py-4">
                    <div className="flex min-w-0 items-center gap-3">
                      <div className={`rounded-2xl p-2.5 ${incoming ? "bg-emerald-50 text-emerald-700" : "bg-rose-50 text-rose-700"}`}>
                        {incoming ? <ArrowDownLeft size={18} /> : <ArrowUpRight size={18} />}
                      </div>
                      <div className="min-w-0">
                        <p className="truncate font-medium text-slate-900">
                          {transaction.description || transaction.category}
                        </p>
                        <p className="truncate text-sm text-slate-500">
                          {incoming ? "From" : "To"} @{transaction.counterparty}
                        </p>
                      </div>
                    </div>
                    <p className={`shrink-0 font-semibold ${incoming ? "text-emerald-700" : "text-slate-900"}`}>
                      {incoming ? "+" : "-"} {money(transaction.amount)}
                    </p>
                  </div>
                );
              })
            )}
          </div>
        </section>

        <section className="rounded-3xl bg-slate-950 p-6 text-white shadow-sm">
          <div className="flex items-center gap-3">
            <div className="rounded-2xl bg-white/10 p-2.5">
              <Landmark size={19} />
            </div>
            <div>
              <p className="text-sm text-slate-400">Financial twin snapshot</p>
              <h2 className="text-lg font-semibold">Analysis-ready</h2>
            </div>
          </div>

          <div className="mt-6 space-y-4">
            <div className="rounded-2xl bg-white/5 p-4">
              <p className="text-sm text-slate-400">Net cash flow</p>
              <p className="mt-1 text-2xl font-semibold">{money(summary.metrics.net_cash_flow)}</p>
            </div>
            <div className="rounded-2xl bg-white/5 p-4">
              <p className="text-sm text-slate-400">Largest expense category</p>
              <p className="mt-1 text-lg font-semibold">
                {summary.metrics.largest_expense_category || "Not enough data"}
              </p>
            </div>
          </div>

          <p className="mt-6 text-sm leading-6 text-slate-400">
            PersonaTwin can consume the same authenticated financial summary API to build and refresh a user's financial digital twin.
          </p>
        </section>
      </div>
    </div>
  );
}

export default Dashboard;
