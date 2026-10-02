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

export default function Statements() {
  const [accounts, setAccounts] = useState([]);
  const [walletAccounts, setWalletAccounts] = useState([]);
  const [statement, setStatement] = useState(null);
  const [accountId, setAccountId] = useState("");
  const [account, setAccount] = useState({
    name: "",
    bank_name: "",
    last_four: "",
    currency: "INR",
    wallet_account_id: "",
  });
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [overrides, setOverrides] = useState({});
  const [page, setPage] = useState(0);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const refresh = async () => {
    const [banks, wallets] = await Promise.all([api.get("/financial/bank-accounts"), api.get("/accounts/")]);
    const data = banks.data;
    setWalletAccounts(wallets.data);
    setAccounts(data);
    setAccountId((current) =>
      data.some((item) => String(item.id) === current)
        ? current
        : data[0]
          ? String(data[0].id)
          : "",
    );
  };
  useEffect(() => {
    refresh()
      .catch((err) => setError(apiError(err)))
      .finally(() => setLoading(false));
  }, []);
  async function action(callback) {
    setError("");
    setMessage("");
    setBusy(true);
    try {
      await callback();
    } catch (err) {
      setError(apiError(err));
    } finally {
      setBusy(false);
    }
  }
  function resetPreview() {
    setPreview(null);
    setOverrides({});
    setPage(0);
  }
  function formData() {
    const data = new FormData();
    data.append("account_id", accountId);
    data.append("file", file);
    return data;
  }
  async function downloadSample() {
    await action(async () => {
      const { data } = await api.get("/financial/sample-statement", {
        responseType: "blob",
      });
      const url = URL.createObjectURL(data);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = "sample-bank-statement.csv";
      anchor.click();
      URL.revokeObjectURL(url);
      setMessage(
        "Sample downloaded. Add a bank account, then upload this fictional statement to review it.",
      );
    });
  }
  async function downloadStatement(item) {
    await action(async () => {
      const { data } = await api.get(`/financial/bank-accounts/${item.id}/statement?format=csv`, { responseType: "blob" });
      const url = URL.createObjectURL(data);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `account-${item.wallet_account_id}-statement.csv`;
      anchor.click();
      URL.revokeObjectURL(url);
    });
  }
  if (loading)
    return <p className="text-slate-500">Loading statement accounts...</p>;
  return (
    <div className="mx-auto max-w-6xl">
      <div className="mb-7 flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.2em] text-blue-600">
            Bring your banking history
          </p>
          <h1 className="mt-2 text-3xl font-bold">Bank statements</h1>
          <p className="mt-2 text-sm text-slate-500">
            Import history into your bank account. Its balance updates, and later transfers appear in your statement.
          </p>
        </div>
        <button
          className={secondaryClass}
          disabled={busy}
          onClick={downloadSample}
        >
          Download sample statement
        </button>
      </div>
      <Notice error={error} message={message} />
      <div className="grid gap-6 lg:grid-cols-[0.85fr_1.15fr]">
        <form
          className={panelClass}
          onSubmit={(event) => {
            event.preventDefault();
            action(async () => {
              const { data } = await api.post(
                "/financial/bank-accounts",
                { ...account, wallet_account_id: account.wallet_account_id ? Number(account.wallet_account_id) : null },
              );
              await refresh();
              setAccountId(String(data.id));
              setAccount({
                name: "",
                bank_name: "",
                last_four: "",
                currency: "INR",
                wallet_account_id: "",
              });
              resetPreview();
              setMessage("Bank account added. Choose its statement to import.");
            });
          }}
        >
          <h2 className="text-xl font-semibold">1. Add a bank account</h2>
          <p className="mt-1 text-sm text-slate-500">
            Use a label and last four digits. Full account numbers are not
            needed.
          </p>
          <div className="mt-5 space-y-4">
            <Field title="Account to populate">
              <select className={inputClass} value={account.wallet_account_id}
                onChange={(event) => setAccount({ ...account, wallet_account_id: event.target.value })}>
                <option value="">Create a new bank account</option>
                {walletAccounts.filter((item) => item.currency === "INR" && !accounts.some((bank) => bank.wallet_account_id === item.id)).map((item) => (
                  <option key={item.id} value={item.id}>{item.name} · {money(item.balance)}</option>
                ))}
              </select>
            </Field>
            <Field title="Account label">
              <input
                className={inputClass}
                maxLength={120}
                value={account.name}
                onChange={(event) =>
                  setAccount({ ...account, name: event.target.value })
                }
                required
                placeholder="Main salary account"
              />
            </Field>
            <Field title="Bank name">
              <input
                className={inputClass}
                maxLength={120}
                value={account.bank_name}
                onChange={(event) =>
                  setAccount({ ...account, bank_name: event.target.value })
                }
                required
                placeholder="Your bank"
              />
            </Field>
            <Field title="Last four digits (optional)">
              <input
                className={inputClass}
                inputMode="numeric"
                pattern="[0-9]{4}"
                maxLength={4}
                value={account.last_four}
                onChange={(event) =>
                  setAccount({ ...account, last_four: event.target.value })
                }
                placeholder="4821"
              />
            </Field>
          </div>
          <button className={`${buttonClass} mt-5`} disabled={busy}>
            Add bank account
          </button>
        </form>
        <form
          className={panelClass}
          onSubmit={(event) => {
            event.preventDefault();
            resetPreview();
            action(async () => {
              const { data } = await api.post(
                "/financial/statements/preview",
                formData(),
              );
              setPreview(data);
            });
          }}
        >
          <h2 className="text-xl font-semibold">2. Upload & review</h2>
          <p className="mt-1 text-sm text-slate-500">
            CSV or unlocked text-table PDF · up to 5 MB / 2,000 rows.
          </p>
          <div className="mt-5 space-y-4">
            <Field title="Statement belongs to">
              <select
                className={inputClass}
                value={accountId}
                required
                disabled={busy || !accounts.length}
                onChange={(event) => {
                  setAccountId(event.target.value);
                  resetPreview();
                }}
              >
                {!accounts.length && (
                  <option value="">Add a bank account first</option>
                )}
                {accounts.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.name} · {item.bank_name}
                  </option>
                ))}
              </select>
            </Field>
            <Field title="Statement file">
              <input
                aria-label="Statement file"
                className={inputClass}
                type="file"
                accept=".csv,.pdf"
                required
                disabled={busy}
                onChange={(event) => {
                  setFile(event.target.files[0] || null);
                  resetPreview();
                }}
              />
            </Field>
          </div>
          <button
            className={`${buttonClass} mt-5`}
            disabled={busy || !file || !accountId}
          >
            {busy ? "Processing..." : "Preview statement"}
          </button>
          <div className="mt-5 rounded-xl bg-slate-50 p-4 text-xs leading-6 text-slate-600">
            <p className="font-semibold">Supported statement columns</p>
            <p>
              Date, Description, Debit, Credit, Balance. Optional: Reference,
              Category. Dates: YYYY-MM-DD or DD/MM/YYYY. Use INR statements.
            </p>
            <p className="mt-2">
              PDFs need a readable transaction table with these headers. For
              scanned or unsupported bank layouts, export to CSV using the
              sample format. Salary and EMI categories are suggestions you can
              correct before import.
            </p>
          </div>
        </form>
      </div>
      {preview && (
        <section className={`${panelClass} mt-6`}>
          <div className="flex flex-wrap justify-between gap-4">
            <div>
              <h2 className="text-xl font-semibold">3. Confirm the import</h2>
              <p className="mt-1 text-sm text-slate-500">
                {preview.period_start} to {preview.period_end} ·{" "}
                {preview.new_rows} new transactions · {preview.duplicate_rows}{" "}
                duplicates skipped
              </p>
            </div>
            <div className="text-sm">
              <p>
                Opening <strong>{money(preview.opening_balance)}</strong>
              </p>
              <p>
                Closing <strong>{money(preview.closing_balance)}</strong>
              </p>
              <p className="mt-2">Account after import <strong>{money(preview.projected_account_balance)}</strong></p>
            </div>
          </div>
          <ul className="mt-4 list-disc space-y-1 pl-5 text-xs leading-5 text-slate-500">
            {preview.warnings.map((warning) => (
              <li key={warning}>{warning}</li>
            ))}
          </ul>
          <div className="mt-5 overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b text-slate-500">
                  {["Date", "Description", "Amount", "Category", "Status"].map(
                    (title) => (
                      <th className="p-2 font-medium" key={title}>
                        {title}
                      </th>
                    ),
                  )}
                </tr>
              </thead>
              <tbody>
                {preview.rows.slice(page * 25, (page + 1) * 25).map((row) => (
                  <tr
                    key={row.row_index}
                    className={`border-b border-slate-100 ${row.duplicate ? "opacity-50" : ""}`}
                  >
                    <td className="whitespace-nowrap p-2">
                      {row.transaction_date}
                    </td>
                    <td className="min-w-48 p-2">
                      <p>{row.description}</p>
                      <p className="text-xs text-slate-400">{row.reference}</p>
                    </td>
                    <td
                      className={`whitespace-nowrap p-2 font-semibold ${row.direction === "INFLOW" ? "text-emerald-700" : "text-slate-900"}`}
                    >
                      {row.direction === "INFLOW" ? "+" : "−"}
                      {money(row.amount)}
                    </td>
                    <td className="p-2">
                      <select
                        aria-label={`Category for transaction ${row.row_index + 1}`}
                        className={`${inputClass} min-w-40 text-xs`}
                        disabled={busy || row.duplicate}
                        value={overrides[row.row_index] || row.category}
                        onChange={(event) =>
                          setOverrides({
                            ...overrides,
                            [row.row_index]: event.target.value,
                          })
                        }
                      >
                        {preview.categories.map((category) => (
                          <option key={category} value={category}>
                            {label(category)}
                          </option>
                        ))}
                      </select>
                    </td>
                    <td className="p-2 text-xs">
                      {row.duplicate ? "Duplicate" : "New"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="mt-4 flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <button
                className={secondaryClass}
                disabled={!page}
                onClick={() => setPage(page - 1)}
              >
                Previous
              </button>
              <span className="text-xs text-slate-500">
                Page {page + 1} / {Math.ceil(preview.rows.length / 25)}
              </span>
              <button
                className={secondaryClass}
                disabled={(page + 1) * 25 >= preview.rows.length}
                onClick={() => setPage(page + 1)}
              >
                Next
              </button>
            </div>
            <button
              className={buttonClass}
              disabled={busy || !preview.new_rows}
              onClick={() =>
                action(async () => {
                  const data = formData();
                  data.append("categories", JSON.stringify(overrides));
                  const result = await api.post(
                    "/financial/statements/import",
                    data,
                  );
                  resetPreview();
                  await refresh();
                  setMessage(
                    `Imported ${result.data.imported_rows} transactions. ${result.data.duplicate_rows} duplicates skipped. Your dashboard is ready.`,
                  );
                })
              }
            >
              Import {preview.new_rows} transactions
            </button>
          </div>
        </section>
      )}
      <section className={`${panelClass} mt-6`}>
        <div className="flex flex-wrap justify-between gap-3">
          <h2 className="text-xl font-semibold">
            Statement accounts & imports
          </h2>
          <Link className="text-sm font-semibold text-blue-600" to="/">
            View financial analysis →
          </Link>
        </div>
        <div className="mt-5 space-y-4">
          {accounts.length ? (
            accounts.map((item) => (
              <article
                key={item.id}
                className="rounded-xl border border-slate-200 p-4"
              >
                <div className="flex flex-wrap justify-between gap-3">
                  <div>
                    <h3 className="font-semibold">{item.name}</h3>
                    <p className="text-xs text-slate-500">
                      {item.bank_name}
                      {item.last_four ? ` · •••• ${item.last_four}` : ""} · INR
                    </p>
                  </div>
                  <div>
                    <p className="text-lg font-bold">
                      {money(item.balance)}
                    </p>
                    <p className="text-xs text-slate-500">
                      Available account balance · account #{item.wallet_account_id}
                    </p>
                  </div>
                </div>
                {item.imports.map((batch) => (
                  <div
                    key={batch.id}
                    className="mt-3 border-t border-slate-100 pt-3 text-xs text-slate-500"
                  >
                    <p className="font-medium text-slate-700">
                      {batch.filename}
                    </p>
                    <p>
                      {batch.period_start} – {batch.period_end} ·{" "}
                      {batch.imported_rows} imported · {batch.duplicate_rows}{" "}
                      duplicates
                    </p>
                  </div>
                ))}
                <div className="mt-4 flex flex-wrap gap-3">
                  <button className={secondaryClass} disabled={busy} onClick={() => action(async () => {
                    const { data } = await api.get(`/financial/bank-accounts/${item.id}/statement`);
                    setStatement(data);
                  })}>View current statement</button>
                  <button className={secondaryClass} disabled={busy} onClick={() => downloadStatement(item)}>Download current CSV</button>
                </div>
                {!item.imports.length && <button
                  className="mt-3 text-xs text-red-600"
                  disabled={busy}
                  onClick={() => {
                    if (
                      window.confirm(
                        `Remove the empty statement setup for ${item.name}? Your bank account stays available.`,
                      )
                    )
                      action(async () => {
                        await api.delete(`/financial/bank-accounts/${item.id}`);
                        resetPreview();
                        await refresh();
                        setMessage(
                          "Statement account and its imported history removed.",
                        );
                      });
                  }}
                >
                  Remove empty setup
                </button>}
              </article>
            ))
          ) : (
            <p className="text-sm text-slate-500">
              No bank statements imported yet.
            </p>
          )}
        </div>
      </section>
      {statement && <section className={`${panelClass} mt-6`}>
        <div className="flex justify-between gap-3"><h2 className="text-xl font-semibold">{statement.account_name} · current statement</h2>
          <button className={secondaryClass} onClick={() => setStatement(null)}>Close</button></div>
        <p className="mt-2 text-sm text-slate-500">Opening {money(statement.opening_balance)} · Current balance {money(statement.closing_balance)} · {statement.transactions.length} transactions</p>
        <div className="mt-4 max-h-[32rem] overflow-auto"><table className="w-full text-left text-sm">
          <thead><tr>{["Date", "Description", "Debit / credit", "Balance", "Source"].map((value) => <th key={value} className="p-2">{value}</th>)}</tr></thead>
          <tbody>{statement.transactions.map((row) => <tr className="border-t" key={`${row.source}-${row.id}`}>
            <td className="whitespace-nowrap p-2">{row.date}</td><td className="p-2">{row.description}</td>
            <td className="whitespace-nowrap p-2">{row.direction === "INFLOW" ? "+" : "−"}{money(row.amount)}</td>
            <td className="whitespace-nowrap p-2">{money(row.balance)}</td><td className="p-2 text-xs">{label(row.source)}</td>
          </tr>)}</tbody></table></div>
      </section>}
    </div>
  );
}
