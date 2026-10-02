# Financial profile and statement analysis

The `/profile` page records take-home salary, other income, employer, occupation,
dependants, a monthly expense budget, and the value of investments, property and
other assets. Keep cash out of the manual asset fields: it is counted separately.
Each loan or mortgage stores lender, original amount, outstanding principal,
annual rate, monthly payment, remaining months and a balance observation date.
Users can add, edit and remove liabilities.

The `/statements` page stores external bank observations separately from wallet
accounts and transfers. An import never changes wallet balances or creates a
spendable wallet transaction. Full account numbers and original file bytes are
not saved; descriptions and references from accepted transactions are retained.

## Statement workflow

1. Create a bank account label (INR only), bank name and optional last four digits.
2. Download the sample or choose your bank's CSV/text-table PDF.
3. Preview the file. No data is persisted at this stage.
4. Review suggested categories on every preview page. Classify own-account
   transfers as `TRANSFER` on both accounts; keep investment contributions as
   `INVESTMENT`. EMI payments remain expenses.
5. Confirm the import. It saves the parsed transactions and import provenance.
6. Open the dashboard. Choose a 1, 3, 6, 12 or 24 month window and optionally an
   end date. The default ends on the latest recorded bank transaction (or wallet
   transaction if no bank statements exist).

CSV headers: `Date,Description,Debit,Credit,Balance,Reference,Category`.
Date, Description, Debit and Credit are required. Supported common aliases include
Transaction Date, Narration, Withdrawal and Deposit. Use UTF-8 and dates in
`YYYY-MM-DD` or day-first `DD/MM/YYYY`. Each row needs exactly one positive debit
or credit, and at most two decimal places. Running balance, reference and category
are optional. When balances are provided, every row must have one and the sequence
must reconcile. Rows must be in chronological or reverse chronological order.
Balances are inferred from the reconciled first and last transactions; the
observation period is the first through last transaction date, not an inferred
statement header period.

PDF support requires a readable transaction table with supported headers. The
sample PDF is supported. Bank-specific layouts, scans and password-protected PDFs
may need a CSV export; OCR is not implemented. Limits: 5 MB, 2,000 transactions,
24 PDF pages. Invalid rows reject the entire file, rather than silently skipping
transactions. Categorization is deterministic keyword matching, not a trained
banking classifier. Categories without a supplied value are suggestions.

Re-uploaded files are rejected. Overlapping statement transactions are skipped
using account-scoped date/reference/direction/amount fingerprints (description
is used when no reference exists). Conflicting amounts on the same dated
reference and direction are rejected. Identical legitimate rows without distinct
references cannot be distinguished and are treated as duplicates; the preview
reports this. The same exact file cannot be added to a second bank account owned
by the user. Distinct files containing the same activity in different bank account
labels cannot always be recognized; label accounts consistently.

Removing a statement account deletes its imported history and balance snapshots.
It does not delete wallet accounts or loans. Demo loading requires no existing
profile, liabilities or statement accounts, so it cannot overwrite real financial
records. The loader creates fictional data only for the signed-in user; it creates
no public demo users or shared passwords.

## Metrics and data provenance

The legacy top-level wallet summary is retained. Its monetary totals are INR only.
The new `financial_twin` object is the financial data contract (schema version 2.0).
When bank records exist, analytics use those records, not a sum of bank records
and wallet transfers. Without bank records, successful external INR wallet
transactions are the fallback; internal wallet transfers and failed/pending
payments are excluded. Imported `TRANSFER` rows are excluded from income and
expense calculations. All selected rows remain in the export for auditing.

Monthly averages divide by the full requested window, including months with no
recorded transactions. Missing and partial months are explicitly flagged. Missing
denominators return `null`, not a manufactured zero-percent ratio. Cash and net
worth can be incomplete when a closing bank balance is unavailable.

| Metric | Definition |
| --- | --- |
| Observed monthly income | Non-transfer bank credits / window months |
| Observed salary | Credits categorized SALARY / window months |
| Expenses | Non-transfer debits excluding investments; includes EMIs |
| Expense ratio | Observed expenses / observed income × 100 |
| Savings rate | (Income − expenses) / income × 100; before investments |
| Net cash flow | Income − expenses − investments; excludes own-account transfers |
| Debt service ratio | Declared monthly loan payments / declared monthly income × 100 |
| Cash | Latest available dated closing balances, or INR wallet cash without statements |
| Net worth | Observed cash + declared asset values − declared outstanding debt |
| Cash runway | Non-negative cash / average expenses |
| Budget remaining | Declared expense budget − observed monthly expenses |

Loan principal and amortization cannot be reconstructed reliably from EMI amounts.
Statements do not automatically reduce principal or determine rate/tenure.
Self-reported assets, profile income and debt are current snapshots, not historical
valuations when a past observation window is selected. Each loan retains its own
balance date; bank balances have `balance_as_of`. Loan and category provenance,
missing data flags and metric definitions travel with the export. This change
provides richer input to PersonaTwin; automatic synchronization to PersonaTwin
is not implemented here.

## API (JWT required)

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET / PUT | `/financial/profile` | Read / replace profile |
| GET / POST | `/financial/liabilities` | List / add loans |
| PUT / DELETE | `/financial/liabilities/{id}` | Edit / remove own liability |
| GET / POST | `/financial/bank-accounts` | List / add external bank accounts |
| DELETE | `/financial/bank-accounts/{id}` | Remove account and its imports |
| POST | `/financial/statements/preview` | Multipart `account_id`, `file`; read-only preview |
| POST | `/financial/statements/import` | Same fields plus optional `categories` JSON object keyed by zero-based row index |
| GET | `/financial/sample-statement?format=csv` | Download fixture; `format=pdf` also supported |
| POST | `/financial/demo` | Explicitly load fixture and fictional financial profile |
| GET | `/integration/financial-summary?months=6&end_date=2026-09-30` | Wallet summary + complete financial twin snapshot |

All queries and mutations are scoped to the authenticated user. Raw uploads are
parsed in a worker thread. Unique constraints protect concurrent same-account
file/transaction imports; conflicts return 409 with no partial import.

## Fictional fixture

`backend/data/sample-bank-statement.csv` and `.pdf` contain 234 transactions,
April–September 2026. Opening balance: INR 125,000. Closing: INR 252,374. Salary
rises from INR 85,000 to INR 90,000 halfway through the period. The fixture has
freelance income, mortgage and education loan EMIs, household spending, mutual
fund SIPs, a self transfer and an unusually large August healthcare expense.
The demo profile includes INR 2,450,000 mortgage principal and INR 180,000
education loan principal, with INR 31,000 combined monthly payments.

Regenerate with `python scripts/generate_sample_statement.py` after installing
the dev requirements. No bank credentials or real customer data are used.

## Deployment and verification

Deploy frontend and backend together from the same updated revision. Before the
backend starts, install requirements and run `alembic upgrade head` from `backend`.
An appropriate Render backend start command is:

```sh
alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Set `DATABASE_URL` to the intended database and `SECRET_KEY` to a private random
string of at least 32 characters. The previous hard-coded signing key has been
removed; missing/short keys now fail startup. Existing tokens signed with the old
key require users to sign in again. Never copy local test credentials into Render.
Keep your frontend Render root/build settings as before. `VITE_API_URL` defaults
to the existing backend URL and can be overridden for local development:

```sh
VITE_API_URL=http://127.0.0.1:8000 npm run dev
```

Validation commands from the repository root:

```sh
pip install -r backend/requirements-dev.txt
PYTHONPATH=backend pytest backend/tests -q
PYTHONPATH=backend python scripts/verify_migrations.py
cd frontend
npm ci
npm run build
npm run lint
```

`verify_migrations.py` uses an isolated temporary SQLite database; it does not
touch Neon. Tests cover CSV/PDF equivalence, imports and overlap deduplication,
atomic failures, cross-user access, profile/debt mutations, calculations and
existing wallet transfers. PostgreSQL migration SQL also compiles offline; a
live Neon migration has not been performed.

The local browser check also exercised signup/login, demo loading, analysis-window
filtering, duplicate preview, PDF upload with category review and confirmation,
liability editing, logout and a 390px mobile layout. It used fictional local users
and a temporary database, not the deployed services.
