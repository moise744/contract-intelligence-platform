# System Design Guide

## Scalability Architecture
To support 10,000 to 1,000,000 documents, the architecture shifts from a monolithic approach to microservices:
1. **API Gateway Layer**: Nginx or AWS API Gateway to handle load balancing.
2. **Stateless App Servers**: Django application running across multiple containers/pods (Kubernetes).
3. **Queueing System**: RabbitMQ or AWS SQS replacing standard Redis for guaranteed message delivery at high volumes.
4. **Data Storage**:
   - Primary Relational Data: Amazon Aurora PostgreSQL.
   - Document Blob Storage: Amazon S3 with lifecycle policies.
   - Vector Search: Pinecone or Elasticsearch for fast semantic similarity over 1M+ chunks.

## Storage Optimization
- Store only original PDFs in S3.
- Database contains extracted metadata, summaries, and chunk references, not the raw binary.
- Extracted text can be compressed or stored in an object store rather than the relational DB to save expensive storage space.

## Processing Optimization
- Batch processing: Instead of real-time processing of massive 500-page documents, use asynchronous queues.
- Map-Reduce summarization: Chunk large documents, summarize chunks in parallel, and reduce into a final executive summary.

## Security Architecture
- **Authentication**: JWT tokens with short expiry, integrated with enterprise SSO (SAML/OAuth2).
- **Authorization**: Row-Level Security (RLS) in PostgreSQL to ensure users only access permitted documents.
- **Encryption**: AES-256 for documents at rest in S3; TLS 1.3 for data in transit.
