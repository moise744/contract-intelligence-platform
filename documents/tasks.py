from celery import shared_task
from .models import Document, DocumentVersion, Summary, RiskAssessment, Clause
from .services import DocumentProcessingService
from .ai_service import AIService

@shared_task
def process_document_task(document_id):
    try:
        document = Document.objects.get(id=document_id)
        document.status = 'processing'
        document.save()

        # Create Version 1
        version = DocumentVersion.objects.create(
            document=document,
            version_number=1,
            file=document.file # In a real app we might copy the file
        )

        # Extract Text
        file_path = document.file.path
        extracted_text = DocumentProcessingService.extract_text_from_pdf(file_path)
        
        version.extracted_text = extracted_text
        version.save()

        # Chunk Text (for later AI processing)
        chunks = DocumentProcessingService.chunk_text(extracted_text)
        print(f"Document {document_id} split into {len(chunks)} chunks.")

        # Trigger AI Processing Pipeline
        ai_service = AIService()
        
        # 1. Summary
        summary_data = ai_service.generate_summary(extracted_text)
        Summary.objects.create(
            document_version=version,
            executive_summary=summary_data.get('executive_summary', ''),
            key_findings=summary_data.get('key_findings', []),
            action_items=summary_data.get('action_items', [])
        )
        
        # 2. Risks
        risks_data = ai_service.detect_risks(extracted_text)
        for r in risks_data:
            RiskAssessment.objects.create(
                document_version=version,
                risk_type=r.get('risk_type', 'General'),
                description=r.get('description', ''),
                risk_level=r.get('risk_level', 'Medium'),
                clause_reference=r.get('clause_reference', '')
            )
            
        # 3. Clauses
        clauses_data = ai_service.extract_clauses(extracted_text)
        for c in clauses_data:
            Clause.objects.create(
                document_version=version,
                clause_type=c.get('clause_type', 'General'),
                text=c.get('text', ''),
                is_standard=c.get('is_standard', True)
            )

        document.status = 'completed'
        document.save()
        
        return f"Processed Document {document_id} successfully."
        
    except Exception as e:
        print(f"Error processing document {document_id}: {e}")
        try:
            doc = Document.objects.get(id=document_id)
            doc.status = 'failed'
            doc.save()
        except:
            pass
        return str(e)
