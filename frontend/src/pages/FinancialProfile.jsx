import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api from "../api";
import { apiError, label, money } from "../utils/financial";
import {
  buttonClass,
  Field,
  inputClass,
  Notice,
  panelClass,
  secondaryClass,
} from "../components/financial/FinancialUI";

const emptyProfile = {
  employer: "",
  occupation: "",
  monthly_salary: 0,
  other_monthly_income: 0,
  monthly_expense_budget: 0,
  investment_value: 0,
  property_value: 0,
  other_asset_value: 0,
  dependants: 0,
};
const emptyLoan = () => ({
  name: "",
  kind: "MORTGAGE",
  lender: "",
  original_amount: "",
  outstanding_amount: "",
  annual_interest_rate: "",
  monthly_payment: "",
  remaining_months: "",
  as_of_date: new Date().toISOString().slice(0, 10),
});
const kinds = [
  "MORTGAGE",
  "PERSONAL_LOAN",
  "EDUCATION_LOAN",
  "VEHICLE_LOAN",
  "CREDIT_CARD",
  "OTHER",
];
const profileFields = [
  ["monthly_salary", "Monthly take-home salary"],
  ["other_monthly_income", "Other monthly income"],
  ["monthly_expense_budget", "Monthly expense budget (including EMIs)"],
  ["investment_value", "Investment portfolio value"],
  ["property_value", "Property market value"],
  ["other_asset_value", "Other assets (excluding account cash)"],
  ["dependants", "Dependants"],
];
const loanFields = [
  ["original_amount", "Original loan amount"],
  ["outstanding_amount", "Outstanding principal"],
  ["annual_interest_rate", "Annual interest rate (%)"],
  ["monthly_payment", "Monthly EMI / payment"],
  ["remaining_months", "Months remaining"],
];

export default function FinancialProfile() {
  const [profile, setProfile] = useState(emptyProfile);
  const [loans, setLoans] = useState([]);
  const [loan, setLoan] = useState(emptyLoan);
  const [editing, setEditing] = useState(null);
  const [showLoan, setShowLoan] = useState(false);
  const [hasProfile, setHasProfile] = useState(false);
  const [bankCount, setBankCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const refresh = async () => {
    const [p, l, b] = await Promise.all([
      api.get("/financial/profile"),
      api.get("/financial/liabilities"),
      api.get("/financial/bank-accounts"),
    ]);
    setProfile(
      Object.fromEntries(
        Object.keys(emptyProfile).map((key) => [
          key,
          p.data.profile?.[key] ?? emptyProfile[key],
        ]),
      ),
    );
    setHasProfile(Boolean(p.data.profile));
    setLoans(l.data);
    setBankCount(b.data.length);
  };
  useEffect(() => {
    refresh()
      .catch((err) => setError(apiError(err)))
      .finally(() => setLoading(false));
  }, []);
  async function mutate(action, success) {
    setBusy(true);
    setError("");
    setMessage("");
    try {
      await action();
      await refresh();
      setMessage(success);
    } catch (err) {
      setError(apiError(err));
    } finally {
      setBusy(false);
    }
  }
  function startLoan(item) {
    setEditing(item?.id ?? null);
    setLoan(
      item
        ? Object.fromEntries(
            Object.keys(emptyLoan()).map((key) => [key, item[key]]),
          )
        : emptyLoan(),
    );
    setShowLoan(true);
    setError("");
    setMessage("");
  }
  async function saveLoan(event) {
    event.preventDefault();
    await mutate(async () => {
      if (editing) await api.put(`/financial/liabilities/${editing}`, loan);
      else await api.post("/financial/liabilities", loan);
      setShowLoan(false);
      setEditing(null);
      setLoan(emptyLoan());
    }, "Liability saved. Your financial analysis now includes it.");
  }
  if (loading)
    return <p className="text-slate-500">Loading your financial profile...</p>;
  return (
    <div className="mx-auto max-w-6xl">
      <div className="mb-7 flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.2em] text-blue-600">
            The bigger picture
          </p>
          <h1 className="mt-2 text-3xl font-bold">Financial profile</h1>
          <p className="mt-2 text-sm text-slate-500">
            Give your twin context beyond transactions. All values are in INR.
          </p>
        </div>
        <Link className={secondaryClass} to="/">
          View analysis
        </Link>
      </div>
      <Notice error={error} message={message} />
      {!hasProfile && !loans.length && !bankCount && (
        <section className="mb-6 rounded-2xl border border-blue-100 bg-blue-50 p-5">
          <h2 className="font-semibold">
            Try a complete fictional financial twin
          </h2>
          <p className="mt-2 text-sm text-slate-600">
            Six months of salary, expenses, home mortgage EMIs, education loan
            payments and investments. Loads only into an empty financial
            profile.
          </p>
          <button
            className={`${buttonClass} mt-4`}
            disabled={busy}
            onClick={() => {
              if (
                window.confirm(
                  "Load fictional demo finances into this account?",
                )
              )
                mutate(
                  () => api.post("/financial/demo"),
                  "Demo finances loaded. Open the dashboard to analyse six months of activity.",
                );
            }}
          >
            Load demo finances
          </button>
        </section>
      )}
      <form
        className={`${panelClass} mb-6`}
        onSubmit={(event) => {
          event.preventDefault();
          mutate(
            () => api.put("/financial/profile", profile),
            "Financial profile saved.",
          );
        }}
      >
        <h2 className="text-xl font-semibold">Income & assets</h2>
        <p className="mt-1 text-sm text-slate-500">
          Self-reported values. Bank statements provide observed income and
          expenses separately.
        </p>
        <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {["employer", "occupation"].map((key) => (
            <Field key={key} title={label(key)}>
              <input
                className={inputClass}
                maxLength={120}
                value={profile[key]}
                onChange={(event) =>
                  setProfile({ ...profile, [key]: event.target.value })
                }
              />
            </Field>
          ))}
          {profileFields.map(([key, title]) => (
            <Field key={key} title={title}>
              <input
                className={inputClass}
                type="number"
                min="0"
                max={key === "dependants" ? 100 : undefined}
                step={key === "dependants" ? "1" : "0.01"}
                required
                value={profile[key]}
                onChange={(event) =>
                  setProfile({ ...profile, [key]: event.target.value })
                }
              />
            </Field>
          ))}
        </div>
        <button className={`${buttonClass} mt-6`} disabled={busy}>
          Save financial profile
        </button>
      </form>
      <section className={panelClass}>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-xl font-semibold">Loans & mortgages</h2>
            <p className="mt-1 text-sm text-slate-500">
              Record each liability's principal, rate, EMI and remaining tenure.
            </p>
          </div>
          <button
            className={secondaryClass}
            disabled={busy}
            onClick={() => startLoan(null)}
          >
            + Add liability
          </button>
        </div>
        {showLoan && (
          <form
            className="mt-6 rounded-xl border border-blue-100 bg-blue-50/40 p-5"
            onSubmit={saveLoan}
          >
            <h3 className="mb-4 font-semibold">
              {editing ? "Edit liability" : "New liability"}
            </h3>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              <Field title="Loan name">
                <input
                  className={inputClass}
                  value={loan.name}
                  maxLength={120}
                  required
                  onChange={(event) =>
                    setLoan({ ...loan, name: event.target.value })
                  }
                  placeholder="Home mortgage"
                />
              </Field>
              <Field title="Type">
                <select
                  className={inputClass}
                  value={loan.kind}
                  onChange={(event) =>
                    setLoan({ ...loan, kind: event.target.value })
                  }
                >
                  {kinds.map((kind) => (
                    <option key={kind} value={kind}>
                      {label(kind)}
                    </option>
                  ))}
                </select>
              </Field>
              <Field title="Lender">
                <input
                  className={inputClass}
                  value={loan.lender}
                  maxLength={120}
                  required
                  onChange={(event) =>
                    setLoan({ ...loan, lender: event.target.value })
                  }
                />
              </Field>
              {loanFields.map(([key, title]) => (
                <Field key={key} title={title}>
                  <input
                    className={inputClass}
                    type="number"
                    min="0"
                    max={
                      key === "remaining_months"
                        ? 600
                        : key === "annual_interest_rate"
                          ? 100
                          : undefined
                    }
                    step={
                      key === "remaining_months"
                        ? 1
                        : key === "annual_interest_rate"
                          ? "0.001"
                          : "0.01"
                    }
                    value={loan[key]}
                    required
                    onChange={(event) =>
                      setLoan({ ...loan, [key]: event.target.value })
                    }
                  />
                </Field>
              ))}
              <Field title="Principal balance as of">
                <input
                  className={inputClass}
                  type="date"
                  value={loan.as_of_date}
                  required
                  onChange={(event) =>
                    setLoan({ ...loan, as_of_date: event.target.value })
                  }
                />
              </Field>
            </div>
            <div className="mt-5 flex gap-3">
              <button className={buttonClass} disabled={busy}>
                Save liability
              </button>
              <button
                type="button"
                className={secondaryClass}
                onClick={() => setShowLoan(false)}
              >
                Cancel
              </button>
            </div>
          </form>
        )}
        <div className="mt-6 grid gap-4 sm:grid-cols-2">
          {loans.length ? (
            loans.map((item) => (
              <article
                key={item.id}
                className="rounded-2xl border border-slate-200 p-5"
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-wide text-blue-600">
                      {label(item.kind)}
                    </p>
                    <h3 className="mt-1 text-lg font-semibold">{item.name}</h3>
                    <p className="text-sm text-slate-500">{item.lender}</p>
                  </div>
                  <button
                    className="text-sm font-semibold text-blue-600"
                    disabled={busy}
                    onClick={() => startLoan(item)}
                  >
                    Edit
                  </button>
                </div>
                <p className="mt-4 text-2xl font-bold">
                  {money(item.outstanding_amount)}
                </p>
                <p className="mt-1 text-xs text-slate-500">
                  Outstanding as of {item.as_of_date} · Original{" "}
                  {money(item.original_amount)}
                </p>
                <div className="mt-4 grid grid-cols-3 gap-2 rounded-xl bg-slate-50 p-3 text-sm">
                  <div>
                    <p className="text-xs text-slate-500">Monthly EMI</p>
                    <p className="mt-1 font-medium">
                      {money(item.monthly_payment)}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-slate-500">Annual rate</p>
                    <p className="mt-1 font-medium">
                      {Number(item.annual_interest_rate)}%
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-slate-500">Remaining</p>
                    <p className="mt-1 font-medium">
                      {item.remaining_months} months
                    </p>
                  </div>
                </div>
                <button
                  className="mt-4 text-xs text-red-600"
                  disabled={busy}
                  onClick={() => {
                    if (
                      window.confirm(
                        `Remove ${item.name} from your financial profile?`,
                      )
                    )
                      mutate(
                        () => api.delete(`/financial/liabilities/${item.id}`),
                        "Liability removed.",
                      );
                  }}
                >
                  Remove liability
                </button>
              </article>
            ))
          ) : (
            <p className="py-4 text-sm text-slate-500">
              No liabilities recorded. Add loans you want included in your twin.
            </p>
          )}
        </div>
      </section>
      <p className="mt-5 text-xs leading-5 text-slate-500">
        EMI payments in statements show cash outflow. Outstanding principal is a
        separate dated value and must be kept up to date manually.
      </p>
    </div>
  );
}
