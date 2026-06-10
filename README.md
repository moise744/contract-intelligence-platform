# Mélange — Enterprise Contract Intelligence Platform

> **Production-grade AI-powered platform for automated contract analysis, risk detection, and document intelligence.**
> Built for law firms, banks, consulting firms, and Fortune 500 enterprises.

---

## 🎯 What This Platform Does

Mélange automates the manual, time-consuming task of reading contracts and legal documents. Upload a PDF, and the AI pipeline automatically:

- **Generates an executive summary** with key findings and action items
- **Detects risks** (Financial, Legal, Compliance, Operational) with severity levels
- **Extracts key clauses** (Termination, Payment, Liability, Confidentiality, etc.)
- **Tracks obligations** with party assignment and deadlines
- **Answers questions** about specific documents via natural language Q&A
- **Enables global search** across all contracts, clauses, and risks

---

## 🏗 Architecture Overview

```
┌────────────────────────────────────────────────────────────────┐
│  Frontend (HTML/CSS/JS)  ←→  Django REST API  ←→  SQLite/PG  │
│                                     │                           │
│                              Celery Worker                      │
│                              (Background AI)                    │
│                                     │                           │
│                         ┌───────────┴──────────┐               │
│                         │   AI Pipeline         │               │
│                         │  • Summarization      │               │
│                         │  • Risk Detection     │               │
│                         │  • Clause Extraction  │               │
│                         │  • Q&A (RAG)          │               │
│                         └──────────────────────-┘               │
└────────────────────────────────────────────────────────────────┘
```

---

## 📦 Technology Stack

| Layer              | Technology                              |
|--------------------|------------------------------------------|
| **Backend**        | Python 3.11, Django 4.2+, Django REST Framework |
| **AI/NLP**         | OpenAI GPT-3.5-turbo, LangChain, LangChain-OpenAI |
| **Document Processing** | PyPDF (text extraction), LangChain TextSplitter |
| **Task Queue**     | Celery + Redis                          |
| **Database**       | SQLite (dev) / PostgreSQL (production)  |
| **Frontend**       | Vanilla HTML/CSS/JS, Chart.js, Font Awesome |
| **Deployment**     | Docker + docker-compose                 |

---

## 🚀 Quick Start (Local Development)

### Prerequisites
- Python 3.11+
- (Optional) Redis — required only if running Celery background workers

### Step 1: Set Up Environment

```powershell
# Navigate to project directory
cd melange3

# Activate virtual environment
.\venv\Scripts\activate

# Install dependencies (already done if venv exists)
pip install -r requirements.txt
```

### Step 2: Configure Environment Variables

Copy the example env file and add your OpenAI API key (optional — mock data works without it):

```powershell
copy .env.example .env
# Edit .env and set OPENAI_API_KEY=sk-...
```

### Step 3: Run Database Migrations

```powershell
python manage.py migrate
```

### Step 4: Create Admin User (Optional)

```powershell
python manage.py createsuperuser
```

### Step 5: Start the Backend Server

```powershell
python manage.py runserver
```

The API will be available at: **http://localhost:8000/api/**

### Step 6: Open the Frontend

Open `frontend/index.html` directly in your browser (double-click), or serve it with:

```powershell
cd frontend
python -m http.server 3000
# Open http://localhost:3000
```

---

## 🧪 Running Tests

```powershell
# Run all 46 tests with detailed output
python manage.py test documents --verbosity=2
```

**Test Coverage:**
- `DocumentModelTests` — UUID primary key, field defaults, status transitions
- `DocumentVersionModelTests` — versioning, text extraction fields
- `RiskAssessmentModelTests` — risk levels, field types
- `SummaryModelTests` — JSON fields, one-to-one constraint
- `AuditLogModelTests` — action tracking
- `DocumentAPITests` — CRUD, filtering, search, upload + task trigger
- `DocumentAnalysisAPITests` — full analysis response structure
- `QAAPITests` — question/answer endpoint
- `DashboardAPITests` — KPI aggregations, chart data
- `SearchAPITests` — cross-entity global search
- `AIServiceTests` — mock output structure and data integrity
- `DocumentProcessingServiceTests` — text chunking
- `SerializerTests` — field presence and types

---

## 🐳 Docker Deployment

Start all services (PostgreSQL + Redis + Django + Celery):

```powershell
docker-compose up --build
```

Then visit **http://localhost:8000**.

---

## 🔌 API Endpoints

| Method | Endpoint                             | Description                          |
|--------|--------------------------------------|--------------------------------------|
| GET    | `/api/documents/`                    | List all documents (filterable)      |
| POST   | `/api/documents/`                    | Upload a new document                |
| GET    | `/api/documents/{id}/`               | Get a single document                |
| DELETE | `/api/documents/{id}/`               | Delete a document                    |
| GET    | `/api/documents/{id}/analysis/`      | Full AI analysis (summary+risks+clauses+obligations) |
| POST   | `/api/documents/{id}/ask/`           | Ask a question about the document    |
| GET    | `/api/dashboard/`                    | KPIs and chart data                  |
| GET    | `/api/search/?q={term}`              | Global search across contracts       |
| GET    | `/api/risks/`                        | List all risks (filterable by level) |
| GET    | `/api/clauses/`                      | List all clauses (searchable)        |
| GET    | `/api/obligations/`                  | List all obligations                 |
| GET    | `/api/audit-logs/`                   | System audit trail                   |

---

## 🔒 Security Notes

- **No OpenAI key required** — the platform uses realistic mock data for demonstration.
- **Authentication** is set to `AllowAny` for demo. In production, switch to `IsAuthenticated` in `settings.py`.
- **CORS** is open for development. Restrict `CORS_ALLOWED_ORIGINS` in production.
- **Never commit** your `.env` file — it is in `.gitignore`.

---

## 📂 Project Structure

```
melange3/
├── config/              # Django project settings, URLs, Celery config
│   ├── settings.py
│   ├── urls.py
│   └── celery.py
├── documents/           # Core application
│   ├── models.py        # Data models (Document, Risk, Clause, Summary, etc.)
│   ├── views.py         # API ViewSets + Dashboard + Search + Q&A
│   ├── serializers.py   # DRF serializers
│   ├── urls.py          # API routing
│   ├── tasks.py         # Celery background task (AI pipeline)
│   ├── ai_service.py    # OpenAI/LangChain wrapper with mock fallback
│   ├── services.py      # PDF text extraction + LangChain chunking
│   ├── admin.py         # Django Admin configuration
│   └── tests.py         # 46-test comprehensive test suite
├── frontend/            # Standalone web interface
│   ├── index.html       # Full SPA with all views
│   ├── styles.css       # Premium glassmorphism design system
│   └── app.js           # Application controller (all API integration)
├── requirements.txt     # Python dependencies
├── docker-compose.yml   # Full stack Docker config
├── Dockerfile           # Application container
└── .env.example         # Environment variable template
```

---

## 👤 User Roles

| Role                | Capabilities                                         |
|---------------------|------------------------------------------------------|
| Legal Team          | Full document analysis, clause review, obligation tracking |
| Executives          | Dashboard KPIs, executive summaries                  |
| Analysts            | Document comparison, search, risk reports            |
| Compliance Officers | Compliance risk tracking, audit logs                 |
| Procurement         | Vendor contract analysis, obligation deadlines       |
| Financial Analysts  | Financial risk detection, payment term extraction    |

---

## 📊 Scalability

| Scale          | Strategy                                              |
|----------------|-------------------------------------------------------|
| 10K docs       | SQLite → PostgreSQL, single server                   |
| 100K docs      | Celery workers, Redis caching, DB indexing           |
| 1M+ docs       | Horizontal Celery scaling, pgvector for semantic search, object storage (S3) for files |

---

*Built as a portfolio demonstration of enterprise AI engineering capabilities.*
