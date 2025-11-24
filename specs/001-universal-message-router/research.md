# Research: Universal Message Router

**Feature**: Universal Message Router
**Date**: 2025-11-23

## Technology Decisions

### 1. Message Broker: Apache Kafka

- **Decision**: Use Apache Kafka for message routing and queuing.
- **Rationale**:
  - Handles high throughput ("millions of users").
  - Decouples ingestion (API) from processing (Routing/Delivery).
  - Provides durability and replayability for reliability.
- **Alternatives Considered**:
  - **RabbitMQ**: Good for complex routing but lower throughput ceiling than Kafka for massive scale.
  - **Redis Pub/Sub**: Fast but lacks durability (fire-and-forget), unacceptable for "Reliability & Persistence" principle.

### 2. Database: MongoDB (NoSQL)

- **Decision**: Use MongoDB for message history and metadata.
- **Rationale**:
  - Flexible schema allows storing diverse message payloads from different platforms (WhatsApp vs Telegram JSON structures).
  - High write throughput for chat logs.
  - Horizontal scalability via sharding.
- **Alternatives Considered**:
  - **PostgreSQL**: Strong consistency, but harder to scale for massive write-heavy chat logs without complex partitioning.
  - **Cassandra**: Excellent for writes, but higher operational complexity for a student project compared to MongoDB.

### 3. File Storage: S3-Compatible (MinIO)

- **Decision**: Use S3-compatible object storage (MinIO for local/dev, AWS S3 for prod).
- **Rationale**:
  - Industry standard for large blobs (2GB files).
  - Offloads file streaming from the API server.
  - Scalable and cost-effective.
- **Alternatives Considered**:
  - **GridFS (MongoDB)**: Storing 2GB files in DB chunks adds significant load to the database.
  - **Local Filesystem**: Does not scale horizontally across multiple API nodes.

### 4. Framework: Python (FastAPI)

- **Decision**: Use Python with FastAPI.
- **Rationale**:
  - Native `asyncio` support is crucial for I/O-bound tasks (waiting for DB, Kafka, S3).
  - Excellent ecosystem for Data/AI (future proofing) and Systems integration.
  - Automatic OpenAPI generation.
- **Alternatives Considered**:
  - **Node.js**: Good alternative, but Python was chosen for ecosystem preference.
  - **Go**: Better raw performance, but steeper learning curve for rapid iteration.

### 5. API Protocol: REST & gRPC

- **Decision**: Expose REST for general clients and gRPC for high-performance internal microservices.
- **Rationale**:
  - **REST**: Universal compatibility for web/mobile clients.
  - **gRPC**: Low latency, typed contracts for internal CLI or service-to-service communication.

## Architecture Patterns

### Adapter Pattern

- **Context**: Supporting multiple external platforms (WhatsApp, Telegram, etc.).
- **Approach**: Define a generic `MessageProvider` interface. Implement adapters for each platform that convert external payloads to the internal `Message` entity.

### Asynchronous Processing

- **Context**: Handling spikes and slow external APIs.
- **Approach**: API accepts message -> Pushes to Kafka -> Returns "Accepted" (202). Worker consumes Kafka -> Calls External API -> Updates DB status.
