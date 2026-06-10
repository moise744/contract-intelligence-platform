# Technical Documentation

## 1. Document Ingestion Pipeline
The document ingestion pipeline is built using Django REST Framework for the API layer and Celery for asynchronous processing.
- **Upload Endpoint**: `POST /api/documents/` accepts multipart form data.
- **Storage**: Files are temporarily stored in local volume, but production deployments should use S3 buckets (via `django-storages`).
- **Processing Task**: `process_document_task(document_id)` runs via Celery worker.
- **Extraction**: `PyPDF` is used for text extraction. OCR (Tesseract) can be integrated as a fallback for scanned PDFs.

## 2. Text Chunking
Long contracts exceed standard LLM context windows. We utilize LangChain's `RecursiveCharacterTextSplitter`.
- **Chunk Size**: 1000 characters.
- **Overlap**: 200 characters to prevent cutting off context mid-sentence.

## 3. AI Service Integration
Located in `documents/ai_service.py`. It utilizes `ChatOpenAI`.
- **Summarization**: Prompt engineering extracts a 3-part JSON (Executive Summary, Key Findings, Action Items).
- **Risk Detection**: LLM is instructed to classify risks based on standard corporate compliance frameworks.

## 4. API Endpoints
- `GET/POST /api/documents/`: Manage documents.
- `GET /api/versions/`: Retrieve document versions and extracted raw text.
- `GET /api/summaries/`: Retrieve generated summaries.
- `GET /api/risks/`: Retrieve identified risks.
- `GET /api/clauses/`: Retrieve extracted clauses.
