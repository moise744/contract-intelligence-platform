from django.contrib import admin
from .models import Document, DocumentVersion, Summary, RiskAssessment, Clause, Obligation, Report, AuditLog


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'uploaded_by', 'uploaded_at')
    list_filter = ('status',)
    search_fields = ('title',)
    readonly_fields = ('id', 'uploaded_at')
    ordering = ('-uploaded_at',)


@admin.register(DocumentVersion)
class DocumentVersionAdmin(admin.ModelAdmin):
    list_display = ('document', 'version_number', 'created_at')
    list_filter = ('version_number',)
    search_fields = ('document__title',)
    readonly_fields = ('id', 'created_at')


@admin.register(Summary)
class SummaryAdmin(admin.ModelAdmin):
    list_display = ('document_version', 'created_at')
    readonly_fields = ('created_at',)
    search_fields = ('document_version__document__title', 'executive_summary')


@admin.register(RiskAssessment)
class RiskAssessmentAdmin(admin.ModelAdmin):
    list_display = ('document_version', 'risk_type', 'risk_level', 'created_at')
    list_filter = ('risk_level', 'risk_type')
    search_fields = ('description', 'risk_type', 'document_version__document__title')
    readonly_fields = ('created_at',)


@admin.register(Clause)
class ClauseAdmin(admin.ModelAdmin):
    list_display = ('document_version', 'clause_type', 'is_standard', 'page_number')
    list_filter = ('clause_type', 'is_standard')
    search_fields = ('text', 'clause_type', 'document_version__document__title')


@admin.register(Obligation)
class ObligationAdmin(admin.ModelAdmin):
    list_display = ('description', 'party_responsible', 'deadline', 'status', 'document_version')
    list_filter = ('status',)
    search_fields = ('description', 'party_responsible')


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('title', 'report_type', 'generated_by', 'generated_at')
    list_filter = ('report_type',)
    search_fields = ('title',)
    readonly_fields = ('generated_at',)


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'timestamp')
    list_filter = ('action',)
    search_fields = ('action', 'user__username')
    readonly_fields = ('timestamp',)
    ordering = ('-timestamp',)
