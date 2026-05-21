#  FastAPI Financial Document Management with Semantic Analysis

A FastAPI application for managing financial documents with AI-powered semantic search using RAG (Retrieval-Augmented Generation).

---

##  Tech Stack

| Layer | Technology |
|---|---|
| Backend Framework | FastAPI |
| Database | PostgreSQL |
| Vector Store | ChromaDB |
| Authentication | JWT Tokens |
| AI / Embeddings | LangChain |
| Document Processing | RAG Pipeline |

---

##  Features

-  Upload, manage, and retrieve financial documents
-  JWT-based authentication with Role-Based Access Control (RBAC)
-  AI-powered semantic search using embeddings
-  ChromaDB vector store for document embeddings
-  Reranking pipeline for improved retrieval accuracy


---

## ⚙️ Setup & Installation


```

### 1. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate        # On Windows: venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file in the root directory:

```env
DATABASE_URL=postgresql://username:password@localhost:5432/financial_docs
SECRET_KEY=your_jwt_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
CHROMA_PERSIST_DIRECTORY=./chroma_db
```

### 4. Run database migrations

```bash
alembic upgrade head
```

### 5. Start the application

```bash
uvicorn app.main:app --reload
```

The API will be available at: `http://localhost:8000`  
Swagger docs: `http://localhost:8000/docs`

---

## 🔐 Authentication APIs

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/auth/register` | Register a new user |
| `POST` | `/auth/login` | User authentication (returns JWT token) |

---

##  Document APIs

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/documents/upload` | Upload a financial document |
| `GET` | `/documents` | Retrieve all documents |
| `GET` | `/documents/{document_id}` | Retrieve document details |
| `DELETE` | `/documents/{document_id}` | Delete a document |
| `GET` | `/documents/search` | Search documents by metadata |

### Document Metadata Schema

```json
{
  "document_id": "uuid",
  "title": "Q3 Financial Report",
  "company_name": "Acme Corp",
  "document_type": "report",
  "uploaded_by": "user_id",
  "created_at": "2024-01-01T00:00:00Z"
}
```

> Supported document types: `invoice`, `report`, `contract`

---

##  Role & User Management APIs

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/roles/create` | Create a new role |
| `POST` | `/users/assign-role` | Assign a role to a user |
| `GET` | `/users/{id}/roles` | Get all roles assigned to a user |
| `GET` | `/users/{id}/permissions` | View permissions for a user |

### Role Permissions Matrix

| Role | Permissions |
|---|---|
| **Admin** | Full access — create, read, update, delete |
| **Financial Analyst** | Upload and edit documents |
| **Auditor** | Review and read documents |
| **Client** | View company-specific documents only |

---

##  RAG (Retrieval-Augmented Generation) APIs

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/rag/index-document` | Generate embeddings and store in ChromaDB |
| `DELETE` | `/rag/remove-document/{id}` | Remove document embeddings from vector store |
| `POST` | `/rag/search` | Perform semantic search |
| `GET` | `/rag/context/{document_id}` | Retrieve related document context |

### Semantic Search Example

**Request:**
```http
POST /rag/search
Content-Type: application/json

{
  "query": "financial risk related to high debt ratio"
}
```

**Response:**
```json
{
  "results": [
    {
      "document_id": "uuid",
      "title": "Annual Risk Report 2023",
      "chunk": "The company's debt-to-equity ratio has risen to 2.3...",
      "score": 0.91
    }
  ]
}
```

---

##  RAG Pipeline

### Document Indexing Pipeline

```
Document Upload
      ↓
Text Extraction
      ↓
Semantic Chunking
      ↓
Embedding Generation (LangChain)
      ↓
Store in ChromaDB
```

### Retrieval & Reranking Pipeline

```
User Query
      ↓
Query Embedding
      ↓
Vector Search (ChromaDB)
      ↓
Top 20 Candidate Results
      ↓
Reranking (Financial Relevance)
      ↓
Top 5 Most Relevant Results
```

---

##  Database Schema Overview

**Users Table**
```
users (id, username, email, hashed_password, created_at)
```

**Documents Table**
```
documents (document_id, title, company_name, document_type, file_path, uploaded_by, created_at)
```

**Roles & Permissions Tables**
```
roles (id, name)
permissions (id, name, description)
role_permissions (role_id, permission_id)
user_roles (user_id, role_id)
```

---

##  Requirements

```txt
fastapi
uvicorn
sqlalchemy
psycopg2-binary
alembic
python-jose[cryptography]
passlib[bcrypt]
python-multipart
langchain
chromadb
sentence-transformers
pydantic
python-dotenv
```

**Your Name**  
[GitHub](https://github.com/your-username) · [LinkedIn](https://linkedin.com/in/your-profile)
