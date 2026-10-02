# Financial profile and statement analysis

The `/profile` page records take-home salary, other income, employer, occupation,
dependants, a monthly expense budget, and the value of investments, property and
other assets. Keep cash out of the manual asset fields: it is counted separately.
Each loan or mortgage stores lender, original amount, outstanding principal,
annual rate, monthly payment, remaining months and a balance observation date.
Users can add, edit and remove liabilities.

Persona Wallet is the user’s simulated bank. The `/statements` page attaches imported
history to a spendable account. Choose an existing owned INR account or create one.
Importing establishes its balance from reconciled history, while retaining subsequent
Persona Wallet transfers. Imports and live transfers compose one account ledger.
Full account numbers and original upload bytes are not retained.

## Statement workflow

1. Choose an existing INR account or create one with a bank name and optional last four digits.
2. Download the sample or choose your bank's CSV/text-table PDF.
3. Preview the file. No data is persisted at this stage.
4. Review suggested categories on every preview page. Classify own-account
   transfers as `TRANSFER` on both accounts; keep investment contributions as
   `INVESTMENT`. EMI payments remain expenses.
5. Confirm the projected account balance. The import posts history and updates spendable funds atomically.
6. Open the dashboard. Choose a 1, 3, 6, 12 or 24 month window and optionally an
   end date. The default ends on the latest transaction in the combined bank ledger.

CSV headers: `Date,Description,Debit,Credit,Balance,Reference,Category`.
Date, Description, Debit, Credit and Balance are required for bank imports. Supported common aliases include
Transaction Date, Narration, Withdrawal and Deposit. Use UTF-8 and dates in
`YYYY-MM-DD` or day-first `DD/MM/YYYY`. Each row needs exactly one positive debit
or credit, and at most two decimal places. Reference and category are optional. Every imported row needs a running balance and the sequence
must reconcile with existing history. Rows must be in chronological or reverse chronological order.
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

Accounts with posted imported history cannot be removed: that history supports the
spendable balance. An empty statement setup can be removed without deleting its
underlying account. Demo loading requires an empty financial profile, liabilities
and statement setup, and creates a funded bank account for the signed-in user.
It does not overwrite existing accounts or create public users/shared passwords.

### Statement updates and overlap

`/accounts/{id}/statement` returns the complete combined history for an owned account.
`/financial/bank-accounts/{id}/statement?format=csv` downloads the latest statement,
including imports and subsequent transfers with running balances. Live payments
retain `WALLET-{transaction_id}` references, allowing exported CSVs to be recognized
on re-upload. An export containing only existing rows is rejected with no changes.

Older backfills must reconcile with existing imported balances and do not reset
newer transfers. A new statement covering posted live payments must contain their
matching WALLET references; ambiguous overlap is rejected instead of posting the
same payment twice. Upload continuous history; unexplained balance gaps are rejected.
The first import replaces a manually entered initial balance with the statement’s
reconciled opening history and closing balance, plus later live transfers. Preview
shows the resulting balance before confirmation. Import/transfer operations lock
account rows on PostgreSQL to prevent lost balance updates.

## Metrics and data provenance

`financial_twin` is the authoritative financial contract (schema version 3.0).
It uses imported history and successful live transfers together. Own-account
transfers appear on both accounts’ statements but are excluded from income and
expense calculations. A transfer to another user is an expense even if its original
category is TRANSFER. Failed/pending transfers are excluded. `account_statements`
contains all recorded account history, while `transactions` uses the selected
analysis window. Legacy wallet-only `metrics`/`transactions` remain for compatibility;
consumers should use `financial_twin` to include imported activity.

Monthly averages divide by the full requested window, including months with no
recorded transactions. Missing and partial months are explicitly flagged. Missing
denominators return `null`, not a manufactured zero-percent ratio. Current cash
is the sum of spendable INR accounts; a past analysis window does not rewind it.

| Metric | Definition |
| --- | --- |
| Observed monthly income | Non-transfer bank credits / window months |
| Observed salary | Credits categorized SALARY / window months |
| Expenses | Non-transfer debits excluding investments; includes EMIs |
| Expense ratio | Observed expenses / observed income × 100 |
| Savings rate | (Income − expenses) / income × 100; before investments |
| Net cash flow | Income − expenses − investments; excludes own-account transfers |
| Debt service ratio | Declared monthly loan payments / declared monthly income × 100 |
| Cash | Current spendable INR account balances, including live transfers |
| Net worth | Current bank cash + declared asset values − declared outstanding debt |
| Cash runway | Non-negative cash / average expenses |
| Budget remaining | Declared expense budget − observed monthly expenses |

Loan principal and amortization cannot be reconstructed reliably from EMI amounts.
Statements do not automatically reduce principal or determine rate/tenure.
Self-reported assets, profile income and debt are current snapshots, not historical
valuations when a past observation window is selected. Each loan retains its own
balance date; bank accounts have current spendable balances. Loan and category provenance,
missing data flags and metric definitions travel with the export. PersonaTwin’s bank integration reads and retains this complete snapshot and
refreshes while its wallet connection is active. Its session token is not stored
in the snapshot. See PersonaTwin’s `docs/bank-ledger-sync.md`.

## API (JWT required)

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET / PUT | `/financial/profile` | Read / replace profile |
| GET / POST | `/financial/liabilities` | List / add loans |
| PUT / DELETE | `/financial/liabilities/{id}` | Edit / remove own liability |
| GET / POST | `/financial/bank-accounts` | List / create or link spendable INR accounts |
| DELETE | `/financial/bank-accounts/{id}` | Remove an empty statement setup; posted history is retained |
| POST | `/financial/statements/preview` | Multipart `account_id`, `file`; read-only preview |
| POST | `/financial/statements/import` | Same fields plus optional `categories` JSON object keyed by zero-based row index |
| GET | `/financial/sample-statement?format=csv` | Download fixture; `format=pdf` also supported |
| GET | `/accounts/{id}/statement` | Full owned account ledger |
| GET | `/financial/bank-accounts/{id}/statement?format=csv` | Download combined statement |
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
touch Neon. The bank-ledger migration creates funded accounts for existing demo
and statement accounts from their latest known closing balance, leaving prior
wallet balances/transfers intact. Existing imports without a closing balance start
at zero and require reconciled history before funding. Tests cover CSV/PDF equivalence, imports and overlap deduplication,
atomic failures, cross-user access, profile/debt mutations, calculations and
existing wallet transfers. PostgreSQL migration SQL also compiles offline; a
live Neon migration has not been performed.

Bank-ledger tests verify funding, transfers on both accounts, updated statements,
CSV round-trip deduplication, older backfills, conflicting imports, account ownership,
and populated migration preservation. No production database was touched.
