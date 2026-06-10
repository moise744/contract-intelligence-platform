from django.db import models
from django.contrib.auth.models import User
import uuid

class Document(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='documents/')
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='uploaded_documents')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, default='pending') # pending, processing, completed, failed
    
    def __str__(self):
        return self.title

class DocumentVersion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='versions')
    version_number = models.IntegerField(default=1)
    file = models.FileField(upload_to='documents/versions/')
    created_at = models.DateTimeField(auto_now_add=True)
    extracted_text = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.document.title} - v{self.version_number}"

class Summary(models.Model):
    document_version = models.OneToOneField(DocumentVersion, on_delete=models.CASCADE, related_name='summary')
    executive_summary = models.TextField()
    key_findings = models.JSONField(default=list)
    action_items = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

class RiskAssessment(models.Model):
    RISK_LEVELS = [('Low', 'Low'), ('Medium', 'Medium'), ('High', 'High')]
    
    document_version = models.ForeignKey(DocumentVersion, on_delete=models.CASCADE, related_name='risks')
    risk_type = models.CharField(max_length=100) # e.g., Financial, Compliance
    description = models.TextField()
    risk_level = models.CharField(max_length=20, choices=RISK_LEVELS)
    clause_reference = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

class Clause(models.Model):
    document_version = models.ForeignKey(DocumentVersion, on_delete=models.CASCADE, related_name='clauses')
    clause_type = models.CharField(max_length=100) # e.g., Termination, Payment
    text = models.TextField()
    page_number = models.IntegerField(null=True, blank=True)
    is_standard = models.BooleanField(default=True)

class Obligation(models.Model):
    document_version = models.ForeignKey(DocumentVersion, on_delete=models.CASCADE, related_name='obligations')
    description = models.TextField()
    party_responsible = models.CharField(max_length=255)
    deadline = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=50, default='open')

class Report(models.Model):
    title = models.CharField(max_length=255)
    report_type = models.CharField(max_length=100)
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    file = models.FileField(upload_to='reports/', null=True, blank=True)
    data = models.JSONField(default=dict)

class AuditLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.JSONField(default=dict)
