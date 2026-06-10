from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DocumentViewSet, DocumentVersionViewSet, SummaryViewSet,
    RiskAssessmentViewSet, ClauseViewSet, ObligationViewSet,
    ReportViewSet, AuditLogViewSet, DashboardViewSet, SearchViewSet
)

router = DefaultRouter()
router.register(r'documents', DocumentViewSet, basename='document')
router.register(r'versions', DocumentVersionViewSet, basename='documentversion')
router.register(r'summaries', SummaryViewSet, basename='summary')
router.register(r'risks', RiskAssessmentViewSet, basename='risk')
router.register(r'clauses', ClauseViewSet, basename='clause')
router.register(r'obligations', ObligationViewSet, basename='obligation')
router.register(r'reports', ReportViewSet, basename='report')
router.register(r'audit-logs', AuditLogViewSet, basename='auditlog')
router.register(r'dashboard', DashboardViewSet, basename='dashboard')
router.register(r'search', SearchViewSet, basename='search')

urlpatterns = [
    path('', include(router.urls)),
]
