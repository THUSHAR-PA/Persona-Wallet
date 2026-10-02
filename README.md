# PersonaWallet 💳

PersonaWallet is a full-stack digital wallet application built with FastAPI, PostgreSQL, SQLAlchemy, Alembic, React, and Vite.

The project manages users, accounts, balances, and transactions. It also provides an integration API for connecting PersonaWallet with the PersonaTwin project.

The financial twin now includes salary and assets, loans and mortgages, reviewed
CSV/PDF bank statement imports, monthly cash flow, expense and debt service ratios,
and a six-month fictional sample. See [Financial twin setup and API](docs/financial-twin.md)
for import formats, calculations, demo data, tests and deployment requirements.

**Backend update:** configure a private `SECRET_KEY` of at least 32 characters and
run `alembic upgrade head` before starting the updated backend. The old hard-coded
JWT key is no longer used.

---

## 🚀 Features

- User registration and authentication
- JWT-based authentication
- Create and manage accounts
- Personal and business accounts
- Transfer money between accounts
- Transfers between different users
- Transaction history
- Account balance tracking
- Financial summary API
- PostgreSQL database
- Database migrations using Alembic
- React frontend with Vite
- PersonaTwin integration support

---

## 🛠️ Tech Stack

### Backend
- Python
- FastAPI
- SQLAlchemy
- PostgreSQL
- Alembic
- Pydantic
- JWT Authentication
- Uvicorn

### Frontend
- React
- Vite
- Axios
- React Router
- Tailwind CSS

---

## 📁 Project Structure

```text
Persona-Wallet/
├── backend/
│   ├── app/
│   │   ├── core/
│   │   ├── models/
│   │   ├── routers/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── main.py
│   ├── alembic/
│   ├── alembic.ini
│   ├── requirements.txt
│   ├── .env
│   └── .env.example
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── vite.config.js
├── .gitignore
└── README.md
```

---

## ⚙️ Prerequisites

Install the following software:

- Python 3.11 or newer
- Node.js and npm
- PostgreSQL
- Git

---

# 🔧 Backend Setup

## 1. Clone the Repository

```bash
git clone https://github.com/THUSHAR-PA/Persona-Wallet.git
cd Persona-Wallet
```

## 2. Navigate to the Backend

```bash
cd backend
```

## 3. Create a Virtual Environment

### Windows

```powershell
python -m venv venv
.\venv\Scripts\activate
```

### Linux/macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

## 4. Install Dependencies

```bash
pip install -r requirements.txt
```

## 5. Configure Environment Variables

Create a `.env` file inside the `backend` directory.

Use `.env.example` as a reference.

Example:

```env
DATABASE_URL=postgresql://username:password@localhost:5432/persona_wallet
SECRET_KEY=replace_with_a_secure_secret
```

Important:
- Never commit your `.env` file.
- Never share database credentials.
- Never commit JWT secrets.
- Each developer should configure their own environment.

## 6. Run Database Migrations

```bash
alembic upgrade head
```

## 7. Start the Backend

```bash
uvicorn app.main:app --reload
```

Backend URL:

```text
http://127.0.0.1:8000
```

Swagger API Documentation:

```text
http://127.0.0.1:8000/docs
```

---

# 🎨 Frontend Setup

Open another terminal.

## 1. Navigate to the Frontend

From the project root:

```bash
cd frontend
```

## 2. Install Dependencies

```bash
npm install
```

## 3. Start the Frontend

```bash
npm run dev
```

The frontend will normally be available at:

```text
http://localhost:5173
```

---

# 🔐 Authentication

The API uses JWT-based authentication.

## Authentication Workflow

1. Register a user.
2. Log in.
3. Receive an access token.
4. Include the token in authenticated requests.

Example:

```http
Authorization: Bearer YOUR_ACCESS_TOKEN
```

Do not share access tokens or private credentials through GitHub, messages, or public repositories.

---

# 📡 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/signup` | Register a user |
| POST | `/auth/login` | Log in |
| GET | `/auth/me` | Get current user |
| GET | `/accounts/` | List accounts |
| POST | `/transactions/` | Create a transaction |
| GET | `/integration/financial-summary` | Get financial summary |

For the complete API specification, open:

```text
http://127.0.0.1:8000/docs
```

---

# 💰 Account Management

PersonaWallet supports:

- Creating accounts
- Viewing account balances
- Personal accounts
- Business accounts
- Managing multiple accounts
- Transferring money between accounts

The application validates account ownership and transaction requirements before processing transfers.

---

# 💸 Transactions

PersonaWallet supports transactions between accounts.

## Supported Functionality

- Transfers between a user's accounts
- Transfers between different users
- Transaction history
- Balance updates
- Transaction categories
- Transaction status tracking

## Transaction Categories

- SALARY
- PURCHASE
- TRANSFER
- RENT
- INVESTMENT
- REFUND
- SUBSCRIPTION
- TAX
- OTHER

Always test transaction functionality after modifying the transaction service or database models.

---

# 🔗 PersonaTwin Integration

PersonaWallet provides an API for integration with PersonaTwin.

## Financial Summary Endpoint

```http
GET /integration/financial-summary
```

The endpoint returns financial information associated with the authenticated user.

### Returned Information

- User details
- User accounts
- Account balances
- Total balance
- Transaction history

### Authentication

This endpoint requires authentication. The request must include a valid JWT access token.

### Integration Purpose

PersonaTwin can use this endpoint to retrieve financial information from PersonaWallet and store the required data in its own database.

The integration should use secure authentication and must not expose private financial information publicly.

---

# 🗃️ Database Migrations

PersonaWallet uses Alembic for database migrations.

## Apply Existing Migrations

```bash
alembic upgrade head
```

## Create a New Migration

After changing SQLAlchemy models:

```bash
alembic revision --autogenerate -m "Describe changes"
```

Apply the migration:

```bash
alembic upgrade head
```

### Migration Guidelines

- Review generated migration files before applying them.
- Do not manually delete migration files without checking dependencies.
- Test migrations on a development database first.
- Keep database schema changes consistent across the team.

---

# 🌍 Environment Configuration

Different environments should use separate configuration values.

| Environment | Database |
|---|---|
| Local development | Local PostgreSQL |
| Teammate development | Individual local PostgreSQL |
| Shared testing | Separate Neon database |
| Production | Production PostgreSQL database |

Recommended practice:

- Use local databases for development.
- Use a separate shared database for testing.
- Never use production credentials locally.
- Store secrets in environment variables.
- Never commit `.env` files.

---

# 👥 Team Development Guidelines

## Branching Strategy

Create a separate branch for each feature or bug fix.

```bash
git checkout -b feature/feature-name
```

Examples:

```text
feature/account-dashboard
feature/transaction-history
feature/personatwin-integration
bugfix/transaction-validation
```

## Before Committing

- Test changes locally.
- Check that the backend starts successfully.
- Check that the frontend runs successfully.
- Check that database migrations work.
- Avoid committing `.env` files.
- Avoid committing passwords, API keys, or tokens.
- Keep commits focused on one change.

## Commit Changes

```bash
git add .
git commit -m "Describe your changes"
git push origin feature/feature-name
```

## Pull Requests

Use pull requests when merging feature branches into the main branch.

Before merging, review the changes and test the affected features.

---

# 🧪 Testing Checklist

Before submitting changes, verify the following:

- [ ] User registration works.
- [ ] User login works.
- [ ] JWT authentication works.
- [ ] Account creation works.
- [ ] Account listing works.
- [ ] Transfers between accounts work.
- [ ] Transfers between different users work.
- [ ] Balances update correctly.
- [ ] Transaction history displays correctly.
- [ ] Frontend communicates with the backend.
- [ ] Database migrations run successfully.
- [ ] Financial summary endpoint works.
- [ ] No credentials are committed to GitHub.

---

# 🔒 Security Guidelines

- Never commit `.env` files.
- Never expose database credentials.
- Never share JWT tokens.
- Use HTTPS for deployed APIs.
- Configure CORS for trusted frontend origins.
- Use separate development and production databases.
- Keep secret keys outside the repository.
- Do not use real banking credentials.
- Avoid storing sensitive personal financial information.
- Validate and authorize every financial operation.
- Do not expose integration endpoints without authentication.

---

# 🚀 Deployment

The backend can be deployed using a cloud hosting platform such as Render.

The production deployment should use:

- A hosted PostgreSQL database
- Environment variables
- HTTPS
- Secure authentication
- Database migrations
- Restricted CORS configuration

## Production Start Command

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### Production Environment Variables

```env
DATABASE_URL=your_production_database_url
SECRET_KEY=your_production_secret_key
```

Never commit production environment variables to GitHub.

---

# 🤝 Contribution Workflow

1. Pull the latest changes.

```bash
git checkout main
git pull origin main
```

2. Create a feature branch.

```bash
git checkout -b feature/your-feature
```

3. Make and test your changes.

4. Commit your changes.

```bash
git add .
git commit -m "Describe your changes"
```

5. Push your branch.

```bash
git push origin feature/your-feature
```

6. Open a pull request.

7. Review and merge the changes after testing.

---

# 📌 Project Status

PersonaWallet is under active development.

The project is intended to serve as a financial data source for the PersonaTwin digital twin platform.

Future improvements may include:

- Advanced financial analytics
- Improved security
- Automated PersonaTwin synchronization
- Financial insights
- Budget tracking
- Deployment automation
- Automated testing
