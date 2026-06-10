from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from django.db.models import Count, Q
from .models import Document, DocumentVersion, Summary, RiskAssessment, Clause, Obligation, Report, AuditLog
from .serializers import (
    DocumentSerializer, DocumentVersionSerializer, SummarySerializer,
    RiskAssessmentSerializer, ClauseSerializer, ObligationSerializer,
    ReportSerializer, AuditLogSerializer
)
from .tasks import process_document_task
from .ai_service import AIService


class DocumentViewSet(viewsets.ModelViewSet):
    """
    Full CRUD for Documents.
    On POST, triggers background Celery task for AI processing.
    Supports filtering by status and title search.
    """
    queryset = Document.objects.all().order_by('-uploaded_at')
    serializer_class = DocumentSerializer
    parser_classes = (MultiPartParser, FormParser)

    def get_queryset(self):
        qs = super().get_queryset()
        status_filter = self.request.query_params.get('status')
        search = self.request.query_params.get('search')
        if status_filter:
            qs = qs.filter(status=status_filter)
        if search:
            qs = qs.filter(title__icontains=search)
        return qs

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        document_id = serializer.data['id']

        # Log audit event
        AuditLog.objects.create(
            action='document_uploaded',
            details={'document_id': str(document_id), 'title': serializer.data.get('title')}
        )

        # Trigger asynchronous AI processing
        process_document_task.delay(document_id)

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=True, methods=['get'], url_path='analysis')
    def analysis(self, request, pk=None):
        """
        Returns the complete AI analysis for a document:
        summary, risks, clauses, and obligations — all in one response.
        """
        document = self.get_object()
        latest_version = document.versions.order_by('-version_number').first()

        if not latest_version:
            return Response({'detail': 'No processed version found.'}, status=status.HTTP_404_NOT_FOUND)

        summary = None
        try:
            summary = SummarySerializer(latest_version.summary).data
        except Summary.DoesNotExist:
            pass

        risks = RiskAssessmentSerializer(latest_version.risks.all(), many=True).data
        clauses = ClauseSerializer(latest_version.clauses.all(), many=True).data
        obligations = ObligationSerializer(latest_version.obligations.all(), many=True).data

        return Response({
            'document': DocumentSerializer(document).data,
            'version': DocumentVersionSerializer(latest_version).data,
            'summary': summary,
            'risks': risks,
            'clauses': clauses,
            'obligations': obligations,
        })

    @action(detail=True, methods=['post'], url_path='ask', parser_classes=[JSONParser, MultiPartParser, FormParser])
    def ask(self, request, pk=None):
        """
        Q&A endpoint: Ask a question about a specific document.
        Uses the AIService with mock fallback if no API key is provided.
        """
        document = self.get_object()
        question = request.data.get('question', '')

        if not question:
            return Response({'detail': 'Question is required.'}, status=status.HTTP_400_BAD_REQUEST)

        latest_version = document.versions.order_by('-version_number').first()
        context_text = latest_version.extracted_text[:8000] if latest_version and latest_version.extracted_text else ''

        ai_service = AIService()
        answer = ai_service.answer_question(context_text, question)

        AuditLog.objects.create(
            action='document_qa',
            details={'document_id': str(document.id), 'question': question}
        )

        return Response({'question': question, 'answer': answer})


class DocumentVersionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DocumentVersion.objects.all().order_by('-created_at')
    serializer_class = DocumentVersionSerializer


class SummaryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Summary.objects.all()
    serializer_class = SummarySerializer


class RiskAssessmentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = RiskAssessment.objects.all().order_by('-created_at')
    serializer_class = RiskAssessmentSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        risk_level = self.request.query_params.get('risk_level')
        search = self.request.query_params.get('search')
        if risk_level:
            qs = qs.filter(risk_level=risk_level)
        if search:
            qs = qs.filter(
                Q(description__icontains=search) |
                Q(risk_type__icontains=search)
            )
        return qs


class ClauseViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Clause.objects.all()
    serializer_class = ClauseSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(
                Q(text__icontains=search) |
                Q(clause_type__icontains=search)
            )
        return qs


class ObligationViewSet(viewsets.ModelViewSet):
    queryset = Obligation.objects.all().order_by('deadline')
    serializer_class = ObligationSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs


class ReportViewSet(viewsets.ModelViewSet):
    queryset = Report.objects.all().order_by('-generated_at')
    serializer_class = ReportSerializer


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditLog.objects.all().order_by('-timestamp')
    serializer_class = AuditLogSerializer


class DashboardViewSet(viewsets.ViewSet):
    """
    Analytics endpoint for the main dashboard.
    Returns aggregated KPIs and chart data.
    """
    def list(self, request):
        total_docs = Document.objects.count()
        processed_docs = Document.objects.filter(status='completed').count()
        high_risks = RiskAssessment.objects.filter(risk_level='High').count()
        upcoming_obligations = Obligation.objects.filter(status='open').count()

        # Risk distribution for chart
        risk_distribution = {
            'High': RiskAssessment.objects.filter(risk_level='High').count(),
            'Medium': RiskAssessment.objects.filter(risk_level='Medium').count(),
            'Low': RiskAssessment.objects.filter(risk_level='Low').count(),
        }

        # Clause type distribution
        clause_types = (
            Clause.objects.values('clause_type')
            .annotate(count=Count('id'))
            .order_by('-count')[:6]
        )

        # Document status distribution
        doc_status_dist = {
            'completed': Document.objects.filter(status='completed').count(),
            'processing': Document.objects.filter(status='processing').count(),
            'pending': Document.objects.filter(status='pending').count(),
            'failed': Document.objects.filter(status='failed').count(),
        }

        # Recent documents
        recent_docs = DocumentSerializer(
            Document.objects.order_by('-uploaded_at')[:5],
            many=True
        ).data

        return Response({
            'kpis': {
                'total_documents': total_docs,
                'processed_documents': processed_docs,
                'high_risks': high_risks,
                'upcoming_obligations': upcoming_obligations,
            },
            'charts': {
                'risk_distribution': risk_distribution,
                'clause_types': list(clause_types),
                'document_status': doc_status_dist,
            },
            'recent_documents': recent_docs,
        })


class SearchViewSet(viewsets.ViewSet):
    """
    Global search across documents, clauses, and risks.
    Query param: q (the search term)
    """
    def list(self, request):
        query = request.query_params.get('q', '').strip()

        if not query:
            return Response({'documents': [], 'clauses': [], 'risks': []})

        documents = Document.objects.filter(title__icontains=query)[:10]
        clauses = Clause.objects.filter(
            Q(text__icontains=query) | Q(clause_type__icontains=query)
        )[:10]
        risks = RiskAssessment.objects.filter(
            Q(description__icontains=query) | Q(risk_type__icontains=query)
        )[:10]

        return Response({
            'documents': DocumentSerializer(documents, many=True).data,
            'clauses': ClauseSerializer(clauses, many=True).data,
            'risks': RiskAssessmentSerializer(risks, many=True).data,
        })
