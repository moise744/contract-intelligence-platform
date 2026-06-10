from rest_framework import serializers
from .models import Document, DocumentVersion, Summary, RiskAssessment, Clause, Obligation, Report, AuditLog


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = '__all__'
        read_only_fields = ('id', 'uploaded_at', 'status')


class DocumentVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentVersion
        fields = '__all__'
        read_only_fields = ('id', 'created_at')


class SummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Summary
        fields = '__all__'
        read_only_fields = ('created_at',)


class RiskAssessmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = RiskAssessment
        fields = '__all__'
        read_only_fields = ('created_at',)


class ClauseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Clause
        fields = '__all__'


class ObligationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Obligation
        fields = '__all__'


class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = '__all__'
        read_only_fields = ('generated_at',)


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = '__all__'
        read_only_fields = ('timestamp',)
