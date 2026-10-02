import { useEffect, useMemo, useState } from "react";
import api from "../api";
import { apiError, label } from "../utils/financial";
import { inputClass, Notice, panelClass, secondaryClass } from "../components/financial/FinancialUI";

export default function History() {
  const [ledgers, setLedgers] = useState([]);
  const [accountId, setAccountId] = useState("");
  const [page, setPage] = useState(0);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    let active = true;
    async function load() {
      try {
        const { data: accounts } = await api.get("/accounts/");
        const responses = await Promise.all(accounts.map((account) => api.get(`/accounts/${account.id}/statement`)));
        if (active) setLedgers(responses.map((response) => response.data));
      } catch (err) { if (active) setError(apiError(err)); }
      finally { if (active) setLoading(false); }
    }
    load();
    return () => { active = false; };
  }, []);
  const rows = useMemo(() => ledgers.filter((ledger) => !accountId || String(ledger.account_id) === accountId)
    .flatMap((ledger) => ledger.transactions.map((row) => ({ ...row, account_name: ledger.account_name, currency: ledger.currency })))
    .sort((a, b) => b.date.localeCompare(a.date) || b.id - a.id), [ledgers, accountId]);
  const amount = (row, value) => new Intl.NumberFormat("en-IN", { style: "currency", currency: row.currency, maximumFractionDigits: 2 }).format(Number(value));
  return <div className="mx-auto max-w-6xl">
    <h1 className="text-3xl font-bold">Account history</h1>
    <p className="mt-2 text-sm text-slate-500">Imported transactions and subsequent bank transfers. Own-account transfers appear on both account statements.</p>
    <Notice error={error} />
    <label className="mt-6 block max-w-sm text-sm">Account
      <select className={`${inputClass} mt-2`} value={accountId} onChange={(event) => { setAccountId(event.target.value); setPage(0); }}>
        <option value="">All accounts</option>{ledgers.map((ledger) => <option key={ledger.account_id} value={ledger.account_id}>{ledger.account_name}</option>)}
      </select>
    </label>
    <section className={`${panelClass} mt-6`}>
      {loading ? <p>Loading account history...</p> : !rows.length ? <p>No posted transactions yet. Import a statement or make a transfer.</p> : <>
        <div className="overflow-x-auto"><table className="w-full text-left text-sm"><thead><tr>{["Date", "Account", "Description", "Category", "Debit / credit", "Balance", "Source"].map((heading) => <th key={heading} className="whitespace-nowrap p-3">{heading}</th>)}</tr></thead>
          <tbody>{rows.slice(page * 25, (page + 1) * 25).map((row) => <tr key={`${row.account_id}-${row.source}-${row.id}`} className="border-t border-slate-100">
            <td className="whitespace-nowrap p-3">{row.date}</td><td className="p-3">{row.account_name}</td><td className="min-w-48 p-3">{row.description}<p className="text-xs text-slate-400">{row.reference}</p></td>
            <td className="p-3">{label(row.category)}</td><td className={`whitespace-nowrap p-3 ${row.direction === "INFLOW" ? "text-emerald-700" : ""}`}>{row.direction === "INFLOW" ? "+" : "−"}{amount(row, row.amount)}</td>
            <td className="whitespace-nowrap p-3">{amount(row, row.balance)}</td><td className="p-3 text-xs">{label(row.source)}</td>
          </tr>)}</tbody></table></div>
        <div className="mt-4 flex items-center gap-4"><button className={secondaryClass} disabled={!page} onClick={() => setPage(page - 1)}>Previous</button><p className="text-sm">Page {page + 1} / {Math.ceil(rows.length / 25)} · {rows.length} entries</p><button className={secondaryClass} disabled={(page + 1) * 25 >= rows.length} onClick={() => setPage(page + 1)}>Next</button></div>
      </>}
    </section>
  </div>;
}
