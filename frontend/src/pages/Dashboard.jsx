import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api from "../api";
import FinancialOverview from "../components/financial/FinancialOverview";
import { apiError, money } from "../utils/financial";
import {
  inputClass,
  Notice,
  panelClass,
  secondaryClass,
} from "../components/financial/FinancialUI";

function Dashboard() {
  const [summary, setSummary] = useState(null);
  const [months, setMonths] = useState(6);
  const [endDate, setEndDate] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    let active = true;
    setLoading(true);
    setError("");
    api
      .get("/integration/financial-summary", {
        params: { months, ...(endDate ? { end_date: endDate } : {}) },
      })
      .then(({ data }) => {
        if (active) setSummary(data);
      })
      .catch((err) => {
        if (active) setError(apiError(err));
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [months, endDate]);
  return (
    <div className="mx-auto max-w-7xl">
      <div className="mb-8 flex flex-wrap items-end justify-between gap-5">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.2em] text-blue-600">
            Persona Wallet / Financial Twin
          </p>
          <h1 className="mt-2 text-3xl font-bold tracking-tight sm:text-4xl">
            Your financial command center
          </h1>
          <p className="mt-2 text-sm text-slate-500">
            Income, spending, assets and debt in one view
            {summary ? ` for @${summary.user.username}` : ""}.
          </p>
        </div>
        <div className="flex flex-wrap items-end gap-3">
          <label className="text-xs text-slate-500">
            Window
            <select
              aria-label="Analysis window"
              className={`${inputClass} mt-1`}
              value={months}
              onChange={(event) => setMonths(Number(event.target.value))}
            >
              {[1, 3, 6, 12, 24].map((value) => (
                <option key={value} value={value}>
                  {value} months
                </option>
              ))}
            </select>
          </label>
          <label className="text-xs text-slate-500">
            End date (latest by default)
            <input
              aria-label="Analysis end date"
              type="date"
              className={`${inputClass} mt-1`}
              value={endDate}
              onChange={(event) => setEndDate(event.target.value)}
            />
          </label>
        </div>
      </div>
      <Notice error={error} />
      {loading ? (
        <p className="py-10 text-slate-500">Loading your financial twin...</p>
      ) : (
        !error &&
        summary && (
          <>
            {summary.financial_twin ? (
              <FinancialOverview twin={summary.financial_twin} />
            ) : (
              <div className={`${panelClass} mb-6`}>
                <h2 className="font-semibold">
                  Financial analysis needs a backend update
                </h2>
                <p className="mt-2 text-sm text-slate-500">
                  Deploy the matching backend branch and run its database
                  migration.
                </p>
              </div>
            )}
            <section className={`${panelClass} mt-6`}>
              <div className="flex flex-wrap justify-between gap-3">
                <div>
                  <h2 className="text-lg font-semibold">Wallet ledger</h2>
                  <p className="mt-1 text-sm text-slate-500">
                    {summary.accounts.length} wallet accounts ·{" "}
                    {summary.metrics.transaction_count} wallet transfers. Bank
                    imports are recorded separately.
                  </p>
                </div>
                <Link to="/accounts" className={secondaryClass}>
                  Manage wallet accounts
                </Link>
              </div>
              <div className="mt-4 flex flex-wrap gap-8 text-sm">
                <p>
                  Wallet cash{" "}
                  <strong className="ml-2">
                    {money(summary.metrics.total_balance)}
                  </strong>
                </p>
                <p>
                  Wallet money in{" "}
                  <strong className="ml-2">
                    {money(summary.metrics.total_inflow)}
                  </strong>
                </p>
                <p>
                  Wallet money out{" "}
                  <strong className="ml-2">
                    {money(summary.metrics.total_outflow)}
                  </strong>
                </p>
              </div>
            </section>
          </>
        )
      )}
    </div>
  );
}
export default Dashboard;
