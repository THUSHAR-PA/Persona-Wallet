export const money = (value) =>
  value == null
    ? "—"
    : new Intl.NumberFormat("en-IN", {
        style: "currency",
        currency: "INR",
        maximumFractionDigits: 0,
      }).format(Number(value));
export const percent = (value) =>
  value == null ? "—" : `${Number(value).toFixed(1)}%`;
export const label = (value) =>
  String(value || "")
    .replaceAll("_", " ")
    .toLowerCase()
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
export function apiError(error) {
  if (error.code === "ECONNABORTED")
    return "The bank service took too long to respond. Please try again shortly.";
  const detail = error.response?.data?.detail;
  if (Array.isArray(detail))
    return detail
      .map((item) => `${item.loc?.slice(1).join(".")}: ${item.msg}`)
      .join(" · ");
  return typeof detail === "string"
    ? detail
    : "Could not complete the request. Please try again.";
}
