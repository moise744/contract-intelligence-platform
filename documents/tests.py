"""
Enterprise Contract Intelligence Platform — Test Suite
=======================================================

Test Coverage:
  - Unit Tests   : Model creation, field validation, defaults
  - API Tests    : REST endpoint responses, CRUD, filtering
  - AI Tests     : Mock service output structure validation
  - Service Tests: PDF extraction, text chunking
  - Integration  : Upload → process → analysis pipeline (mock)

Run with:
    python manage.py test documents --verbosity=2
"""

import uuid
import json
from unittest.mock import patch, MagicMock

from django.test import TestCase
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile

from rest_framework.test import APIClient
from rest_framework import status

from .models import Document, DocumentVersion, Summary, RiskAssessment, Clause, Obligation, Report, AuditLog
from .ai_service import AIService
from .services import DocumentProcessingService
from .serializers import DocumentSerializer, RiskAssessmentSerializer


# =============================================================================
# 1. MODEL UNIT TESTS
# =============================================================================

class DocumentModelTests(TestCase):
    """Tests for the Document model — field defaults, UUID primary key, __str__."""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')

    def test_document_creation_with_uuid(self):
        """Document should be created with a UUID primary key."""
        doc = Document.objects.create(title='Service Agreement 2024', uploaded_by=self.user)
        self.assertIsInstance(doc.id, uuid.UUID)
        self.assertEqual(doc.title, 'Service Agreement 2024')

    def test_document_default_status_is_pending(self):
        """Newly created documents should have 'pending' status."""
        doc = Document.objects.create(title='Vendor Contract')
        self.assertEqual(doc.status, 'pending')

    def test_document_str_returns_title(self):
        """__str__ should return the document title."""
        doc = Document.objects.create(title='Employment Agreement')
        self.assertEqual(str(doc), 'Employment Agreement')

    def test_document_status_choices(self):
        """Document status should be updatable through all valid states."""
        doc = Document.objects.create(title='Test Doc')
        for s in ['processing', 'completed', 'failed']:
            doc.status = s
            doc.save()
            doc.refresh_from_db()
            self.assertEqual(doc.status, s)


class DocumentVersionModelTests(TestCase):
    """Tests for DocumentVersion — versioning, extracted_text field."""

    def setUp(self):
        self.doc = Document.objects.create(title='Annual Report 2024')

    def test_version_creation(self):
        """DocumentVersion should link correctly to its parent Document."""
        ver = DocumentVersion.objects.create(document=self.doc, version_number=1)
        self.assertEqual(ver.document, self.doc)
        self.assertEqual(ver.version_number, 1)

    def test_version_str(self):
        ver = DocumentVersion.objects.create(document=self.doc, version_number=1)
        self.assertIn('Annual Report 2024', str(ver))
        self.assertIn('v1', str(ver))

    def test_extracted_text_nullable(self):
        """extracted_text should be nullable by default."""
        ver = DocumentVersion.objects.create(document=self.doc, version_number=1)
        self.assertIsNone(ver.extracted_text)


class RiskAssessmentModelTests(TestCase):
    """Tests for the RiskAssessment model — risk levels, types."""

    def setUp(self):
        self.doc = Document.objects.create(title='Procurement Contract')
        self.version = DocumentVersion.objects.create(document=self.doc, version_number=1)

    def test_risk_creation(self):
        risk = RiskAssessment.objects.create(
            document_version=self.version,
            risk_type='Financial',
            description='Uncapped liability clause.',
            risk_level='High'
        )
        self.assertEqual(risk.risk_level, 'High')
        self.assertEqual(risk.risk_type, 'Financial')

    def test_all_risk_levels_valid(self):
        """All three risk levels should be storable."""
        for level in ['Low', 'Medium', 'High']:
            risk = RiskAssessment.objects.create(
                document_version=self.version,
                risk_type='Test',
                description='Test description',
                risk_level=level
            )
            self.assertEqual(risk.risk_level, level)


class SummaryModelTests(TestCase):
    """Tests for Summary model — JSON fields, one-to-one relationship."""

    def setUp(self):
        self.doc = Document.objects.create(title='Financial Report')
        self.version = DocumentVersion.objects.create(document=self.doc, version_number=1)

    def test_summary_creation_with_json_fields(self):
        """Summary should store key_findings and action_items as JSON lists."""
        summary = Summary.objects.create(
            document_version=self.version,
            executive_summary='Contract covers 36-month managed IT services.',
            key_findings=['Contract value: $1.8M', 'Term: 36 months'],
            action_items=['Review Section 8.3', 'Confirm payment schedule']
        )
        self.assertIsInstance(summary.key_findings, list)
        self.assertEqual(len(summary.key_findings), 2)
        self.assertIn('Contract value: $1.8M', summary.key_findings)

    def test_summary_one_to_one_constraint(self):
        """A DocumentVersion should not be able to have two summaries."""
        Summary.objects.create(
            document_version=self.version,
            executive_summary='First summary.'
        )
        from django.db import IntegrityError
        with self.assertRaises(Exception):
            Summary.objects.create(
                document_version=self.version,
                executive_summary='Duplicate summary.'
            )


class AuditLogModelTests(TestCase):
    """Tests for AuditLog — action tracking."""

    def test_audit_log_creation(self):
        log = AuditLog.objects.create(
            action='document_uploaded',
            details={'document_id': 'abc-123', 'title': 'NDA Agreement'}
        )
        self.assertEqual(log.action, 'document_uploaded')
        self.assertIsNotNone(log.timestamp)


# =============================================================================
# 2. API ENDPOINT TESTS
# =============================================================================

class DocumentAPITests(TestCase):
    """Tests for the /api/documents/ endpoints."""

    def setUp(self):
        self.client = APIClient()

    def test_list_documents_returns_200(self):
        """GET /api/documents/ should return 200 with a list."""
        Document.objects.create(title='Contract A')
        Document.objects.create(title='Contract B')
        response = self.client.get('/api/documents/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_list_documents_empty(self):
        """GET /api/documents/ should return empty list when no docs exist."""
        response = self.client.get('/api/documents/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_retrieve_single_document(self):
        """GET /api/documents/{id}/ should return the correct document."""
        doc = Document.objects.create(title='NDA Agreement')
        response = self.client.get(f'/api/documents/{doc.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'NDA Agreement')

    def test_document_status_filter(self):
        """GET /api/documents/?status=completed should only return completed docs."""
        Document.objects.create(title='Done Doc', status='completed')
        Document.objects.create(title='Pending Doc', status='pending')
        response = self.client.get('/api/documents/?status=completed')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Done Doc')

    def test_document_search_filter(self):
        """GET /api/documents/?search=vendor should filter by title."""
        Document.objects.create(title='Vendor Agreement')
        Document.objects.create(title='Employment Contract')
        response = self.client.get('/api/documents/?search=vendor')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    @patch('documents.views.process_document_task')
    def test_upload_document_triggers_task(self, mock_task):
        """POST /api/documents/ should create doc and trigger background task."""
        mock_task.delay = MagicMock()
        fake_file = SimpleUploadedFile('test.pdf', b'%PDF-1.4 fake content', content_type='application/pdf')
        response = self.client.post('/api/documents/', {
            'title': 'Test Upload',
            'file': fake_file
        }, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'Test Upload')
        mock_task.delay.assert_called_once()

    def test_delete_document(self):
        """DELETE /api/documents/{id}/ should remove the document."""
        doc = Document.objects.create(title='To Delete')
        response = self.client.delete(f'/api/documents/{doc.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Document.objects.filter(id=doc.id).exists())


class DocumentAnalysisAPITests(TestCase):
    """Tests for the /api/documents/{id}/analysis/ action endpoint."""

    def setUp(self):
        self.client = APIClient()
        self.doc = Document.objects.create(title='Service Level Agreement', status='completed')
        self.version = DocumentVersion.objects.create(
            document=self.doc,
            version_number=1,
            extracted_text='This is a managed IT services contract valued at $1.8M.'
        )

    def test_analysis_returns_200_with_summary(self):
        """GET /api/documents/{id}/analysis/ returns full analysis when completed."""
        Summary.objects.create(
            document_version=self.version,
            executive_summary='36-month managed IT agreement.',
            key_findings=['$1.8M total value'],
            action_items=['Review Section 8.3']
        )
        response = self.client.get(f'/api/documents/{self.doc.id}/analysis/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('document', response.data)
        self.assertIn('summary', response.data)
        self.assertIn('risks', response.data)
        self.assertIn('clauses', response.data)
        self.assertIn('obligations', response.data)

    def test_analysis_returns_404_when_no_version(self):
        """GET /api/documents/{id}/analysis/ returns 404 if no version exists."""
        doc_no_version = Document.objects.create(title='Empty Doc')
        response = self.client.get(f'/api/documents/{doc_no_version.id}/analysis/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class QAAPITests(TestCase):
    """Tests for the /api/documents/{id}/ask/ endpoint."""

    def setUp(self):
        self.client = APIClient()
        self.doc = Document.objects.create(title='SLA Contract')
        self.version = DocumentVersion.objects.create(
            document=self.doc,
            version_number=1,
            extracted_text='This contract terminates with 90 days notice.'
        )

    def test_ask_returns_answer(self):
        """POST /api/documents/{id}/ask/ should return an answer."""
        response = self.client.post(
            f'/api/documents/{self.doc.id}/ask/',
            {'question': 'What is the termination notice period?'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('answer', response.data)
        self.assertIn('question', response.data)

    def test_ask_without_question_returns_400(self):
        """POST /api/documents/{id}/ask/ without 'question' should return 400."""
        response = self.client.post(
            f'/api/documents/{self.doc.id}/ask/',
            {},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class DashboardAPITests(TestCase):
    """Tests for the /api/dashboard/ analytics endpoint."""

    def setUp(self):
        self.client = APIClient()
        # Seed data
        doc = Document.objects.create(title='Annual Report', status='completed')
        version = DocumentVersion.objects.create(document=doc, version_number=1)
        RiskAssessment.objects.create(
            document_version=version,
            risk_type='Financial',
            description='High penalty clause.',
            risk_level='High'
        )
        Obligation.objects.create(
            document_version=version,
            description='Submit quarterly report.',
            party_responsible='Client',
            status='open'
        )

    def test_dashboard_returns_kpis(self):
        """GET /api/dashboard/ should return KPI data."""
        response = self.client.get('/api/dashboard/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('kpis', response.data)
        self.assertIn('charts', response.data)
        self.assertIn('recent_documents', response.data)
        self.assertEqual(response.data['kpis']['total_documents'], 1)
        self.assertEqual(response.data['kpis']['high_risks'], 1)
        self.assertEqual(response.data['kpis']['upcoming_obligations'], 1)

    def test_dashboard_risk_distribution(self):
        """Dashboard chart data should include risk distribution."""
        response = self.client.get('/api/dashboard/')
        dist = response.data['charts']['risk_distribution']
        self.assertEqual(dist['High'], 1)
        self.assertEqual(dist['Medium'], 0)
        self.assertEqual(dist['Low'], 0)


class SearchAPITests(TestCase):
    """Tests for the /api/search/?q= endpoint."""

    def setUp(self):
        self.client = APIClient()
        doc = Document.objects.create(title='Vendor Agreement')
        version = DocumentVersion.objects.create(document=doc, version_number=1)
        Clause.objects.create(
            document_version=version,
            clause_type='Termination',
            text='Either party may terminate with 90 days notice.'
        )
        RiskAssessment.objects.create(
            document_version=version,
            risk_type='Compliance',
            description='Missing GDPR clause in data agreement.',
            risk_level='Medium'
        )

    def test_search_finds_document_by_title(self):
        response = self.client.get('/api/search/?q=vendor')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['documents']), 1)

    def test_search_finds_clause_by_text(self):
        response = self.client.get('/api/search/?q=terminate')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data['clauses']), 0)

    def test_search_finds_risk_by_description(self):
        response = self.client.get('/api/search/?q=GDPR')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data['risks']), 0)

    def test_empty_search_returns_empty_lists(self):
        response = self.client.get('/api/search/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['documents'], [])
        self.assertEqual(response.data['clauses'], [])
        self.assertEqual(response.data['risks'], [])


# =============================================================================
# 3. AI SERVICE VALIDATION TESTS
# =============================================================================

class AIServiceTests(TestCase):
    """Tests for AIService mock outputs — validates JSON structure integrity."""

    def setUp(self):
        # No OPENAI_API_KEY in test env → always uses mock
        self.ai = AIService()

    def test_generate_summary_returns_dict_with_required_keys(self):
        result = self.ai.generate_summary('Contract text here.')
        self.assertIsInstance(result, dict)
        self.assertIn('executive_summary', result)
        self.assertIn('key_findings', result)
        self.assertIn('action_items', result)

    def test_generate_summary_executive_summary_is_string(self):
        result = self.ai.generate_summary('Some text')
        self.assertIsInstance(result['executive_summary'], str)
        self.assertGreater(len(result['executive_summary']), 0)

    def test_generate_summary_findings_is_non_empty_list(self):
        result = self.ai.generate_summary('Some text')
        self.assertIsInstance(result['key_findings'], list)
        self.assertGreater(len(result['key_findings']), 0)

    def test_detect_risks_returns_list(self):
        result = self.ai.detect_risks('Contract text here.')
        self.assertIsInstance(result, list)

    def test_detect_risks_each_item_has_required_keys(self):
        result = self.ai.detect_risks('Contract text here.')
        for risk in result:
            self.assertIn('risk_type', risk)
            self.assertIn('description', risk)
            self.assertIn('risk_level', risk)
            self.assertIn('clause_reference', risk)

    def test_detect_risks_levels_are_valid(self):
        """Risk levels should only be High, Medium, or Low."""
        result = self.ai.detect_risks('Contract text here.')
        for risk in result:
            self.assertIn(risk['risk_level'], ['High', 'Medium', 'Low'])

    def test_extract_clauses_returns_list(self):
        result = self.ai.extract_clauses('Contract text here.')
        self.assertIsInstance(result, list)

    def test_extract_clauses_each_item_has_required_keys(self):
        result = self.ai.extract_clauses('Contract text here.')
        for clause in result:
            self.assertIn('clause_type', clause)
            self.assertIn('text', clause)
            self.assertIn('is_standard', clause)

    def test_extract_clauses_is_standard_is_boolean(self):
        result = self.ai.extract_clauses('Contract text here.')
        for clause in result:
            self.assertIsInstance(clause['is_standard'], bool)

    def test_answer_question_returns_string(self):
        result = self.ai.answer_question('This contract terminates with 90 days notice.', 'What is the termination notice?')
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    def test_answer_question_contains_termination_info(self):
        """Mock Q&A should return termination info when asked about termination."""
        result = self.ai.answer_question('', 'What is the termination clause?')
        self.assertIn('termination', result.lower())


# =============================================================================
# 4. DOCUMENT PROCESSING SERVICE TESTS
# =============================================================================

class DocumentProcessingServiceTests(TestCase):
    """Tests for text chunking logic."""

    def test_chunk_text_returns_list(self):
        text = 'This is a test sentence. ' * 100
        chunks = DocumentProcessingService.chunk_text(text)
        self.assertIsInstance(chunks, list)
        self.assertGreater(len(chunks), 0)

    def test_chunk_text_empty_string(self):
        chunks = DocumentProcessingService.chunk_text('')
        self.assertIsInstance(chunks, list)

    def test_chunk_text_respects_chunk_size(self):
        """Each chunk should be smaller than the configured chunk size."""
        text = 'Word ' * 2000
        chunks = DocumentProcessingService.chunk_text(text, chunk_size=500)
        for chunk in chunks:
            self.assertLessEqual(len(chunk), 600)  # Allow for overlap

    def test_chunk_text_with_overlap(self):
        """Chunking with overlap should produce more chunks."""
        text = 'This is a test. ' * 200
        chunks_no_overlap = DocumentProcessingService.chunk_text(text, chunk_size=200, chunk_overlap=0)
        chunks_with_overlap = DocumentProcessingService.chunk_text(text, chunk_size=200, chunk_overlap=50)
        # Overlap creates more chunks
        self.assertGreaterEqual(len(chunks_with_overlap), len(chunks_no_overlap))


# =============================================================================
# 5. SERIALIZER TESTS
# =============================================================================

class SerializerTests(TestCase):
    """Tests for DRF serializer output shape."""

    def test_document_serializer_contains_expected_fields(self):
        doc = Document.objects.create(title='Test Document')
        serializer = DocumentSerializer(doc)
        data = serializer.data
        self.assertIn('id', data)
        self.assertIn('title', data)
        self.assertIn('status', data)
        self.assertIn('uploaded_at', data)

    def test_risk_assessment_serializer(self):
        doc = Document.objects.create(title='Contract')
        version = DocumentVersion.objects.create(document=doc, version_number=1)
        risk = RiskAssessment.objects.create(
            document_version=version,
            risk_type='Legal',
            description='Unilateral amendment right.',
            risk_level='Medium'
        )
        serializer = RiskAssessmentSerializer(risk)
        data = serializer.data
        self.assertIn('risk_type', data)
        self.assertIn('risk_level', data)
        self.assertIn('description', data)
