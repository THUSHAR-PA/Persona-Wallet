import { Link } from "react-router-dom";
import { money, percent, label } from "../../utils/financial";
import { Metric, panelClass } from "./FinancialUI";

export default function FinancialOverview({ twin }) {
  const m = twin.metrics;
  const categories = twin.category_spend;
  const largest = Math.max(...categories.map((item) => Number(item.amount)), 1);
  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Metric
          title="Observed monthly income"
          value={money(m.observed_monthly_income)}
          hint={`Salary ${money(m.observed_monthly_salary)} · ${twin.period.months}-month average`}
        />
        <Metric
          title="Monthly expenses"
          value={money(m.monthly_expenses)}
          hint="Includes EMIs. Excludes investments and own-account transfers."
        />
        <Metric
          title="Expense / income"
          value={percent(m.expense_to_income_percent)}
          hint="Based on observed transactions, not declared salary."
        />
        <Metric
          title="Savings rate"
          value={percent(m.savings_rate_percent)}
          hint="Surplus before investment contributions."
        />
        <Metric
          title="Outstanding debt"
          value={money(m.total_outstanding_debt)}
          hint={`Mortgage ${money(m.mortgage_outstanding)} · self-reported`}
        />
        <Metric
          title="Monthly debt payments"
          value={money(m.declared_monthly_emi)}
          hint={`Debt service / declared income: ${percent(m.debt_service_to_income_percent)}`}
        />
        <Metric
          title="Observed cash"
          value={money(m.cash_balance)}
          hint="Latest dated bank snapshots, or INR wallet cash without statements."
        />
        <Metric
          title="Estimated net worth"
          value={money(m.estimated_net_worth)}
          hint="Cash + declared assets − declared debt. Snapshot estimate."
          dark
        />
      </div>
      <div className="grid gap-6 xl:grid-cols-[1.5fr_1fr]">
        <section className={panelClass}>
          <h2 className="text-xl font-semibold">Monthly cash flow</h2>
          <p className="mt-1 text-sm text-slate-500">
            {twin.period.start} to {twin.period.end} ·{" "}
            {label(twin.analysis_source)}
          </p>
          <div className="mt-5 overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-slate-200 text-slate-500">
                  {[
                    "Month",
                    "Income",
                    "Expenses",
                    "Investments",
                    "Net cash",
                  ].map((title) => (
                    <th
                      key={title}
                      className="whitespace-nowrap px-2 py-3 font-medium"
                    >
                      {title}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {twin.monthly_cash_flow.map((row) => (
                  <tr
                    key={row.month}
                    className="border-b border-slate-100 last:border-0"
                  >
                    <td className="px-2 py-4 font-medium">{row.month}</td>
                    <td className="whitespace-nowrap px-2 py-4 text-emerald-700">
                      {money(row.income)}
                    </td>
                    <td className="whitespace-nowrap px-2 py-4">
                      {money(row.expenses)}
                    </td>
                    <td className="whitespace-nowrap px-2 py-4">
                      {money(row.investments)}
                    </td>
                    <td
                      className={`whitespace-nowrap px-2 py-4 font-semibold ${Number(row.net_cash_flow) < 0 ? "text-red-600" : "text-blue-700"}`}
                    >
                      {money(row.net_cash_flow)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="mt-5 grid gap-3 sm:grid-cols-3">
            {[
              ["Monthly net cash", money(m.monthly_net_cash_flow)],
              [
                "Cash runway",
                m.cash_runway_months == null
                  ? "—"
                  : `${Number(m.cash_runway_months).toFixed(1)} months`,
              ],
              ["Budget remaining", money(m.budget_variance)],
            ].map(([title, value]) => (
              <div key={title} className="rounded-xl bg-slate-50 p-3">
                <p className="text-xs text-slate-500">{title}</p>
                <p className="mt-1 font-semibold">{value}</p>
              </div>
            ))}
          </div>
        </section>
        <section className={panelClass}>
          <h2 className="text-xl font-semibold">Where money goes</h2>
          <p className="mt-1 text-sm text-slate-500">
            Expense categories across the selected period.
          </p>
          <div className="mt-5 space-y-4">
            {categories.length ? (
              categories.slice(0, 7).map((item) => (
                <div key={item.category}>
                  <div className="mb-1.5 flex justify-between gap-2 text-sm">
                    <span>{label(item.category)}</span>
                    <span className="font-semibold">{money(item.amount)}</span>
                  </div>
                  <div className="h-2 rounded-full bg-slate-100">
                    <div
                      className="h-2 rounded-full bg-blue-500"
                      style={{
                        width: `${(Number(item.amount) / largest) * 100}%`,
                      }}
                    />
                  </div>
                </div>
              ))
            ) : (
              <p className="text-sm text-slate-500">
                Upload a statement to see your spending breakdown.
              </p>
            )}
          </div>
        </section>
      </div>
      <section className="rounded-2xl border border-blue-100 bg-blue-50/60 p-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 className="font-semibold text-slate-900">What your twin knows</h2>
          <div className="flex gap-4 text-sm font-semibold text-blue-700">
            <Link to="/profile">Edit financial profile</Link>
            <Link to="/statements">Import statements</Link>
          </div>
        </div>
        <p className="mt-2 text-sm text-slate-600">
          {m.transaction_count} transactions · {m.months_with_activity}/
          {twin.period.months} months with activity ·{" "}
          {twin.data_quality.statement_count} imports ·{" "}
          {twin.liabilities.length} liabilities
        </p>
        <ul className="mt-3 list-disc space-y-1 pl-5 text-xs leading-5 text-slate-600">
          {twin.data_quality.flags.map((flag) => (
            <li key={flag}>{flag}</li>
          ))}
        </ul>
      </section>
    </div>
  );
}
