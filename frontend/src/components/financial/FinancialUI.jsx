export const inputClass =
  "w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-slate-900 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100";
export const buttonClass =
  "rounded-xl bg-blue-600 px-5 py-2.5 font-semibold text-white hover:bg-blue-700 disabled:cursor-wait disabled:opacity-50";
export const secondaryClass =
  "rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-50";
export const panelClass =
  "min-w-0 rounded-2xl border border-slate-200 bg-white p-5 sm:p-6 shadow-sm";
export function Field({ title, children, hint }) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-sm font-medium text-slate-700">
        {title}
      </span>
      {children}
      {hint && (
        <span className="mt-1 block text-xs text-slate-500">{hint}</span>
      )}
    </label>
  );
}
export function Notice({ error, message }) {
  return (
    <>
      {error && (
        <p
          role="alert"
          className="mb-5 rounded-xl bg-red-50 p-4 text-sm text-red-700"
        >
          {error}
        </p>
      )}
      {message && (
        <p
          role="status"
          className="mb-5 rounded-xl bg-emerald-50 p-4 text-sm text-emerald-800"
        >
          {message}
        </p>
      )}
    </>
  );
}
export function Metric({ title, value, hint, dark = false }) {
  return (
    <div
      className={`rounded-2xl border p-5 ${dark ? "border-slate-900 bg-slate-950 text-white" : "border-slate-200 bg-white"}`}
    >
      <p className={`text-sm ${dark ? "text-slate-300" : "text-slate-500"}`}>
        {title}
      </p>
      <p className="mt-3 text-2xl font-bold tracking-tight">{value}</p>
      {hint && (
        <p
          className={`mt-2 text-xs leading-5 ${dark ? "text-slate-400" : "text-slate-500"}`}
        >
          {hint}
        </p>
      )}
    </div>
  );
}
