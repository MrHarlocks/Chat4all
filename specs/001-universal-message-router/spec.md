# Feature Specification: Universal Message Router

**Feature Branch**: `001-universal-message-router`
**Created**: 2025-11-23
**Status**: Draft
**Input**: User description: "Sou um estudante de sistemas de informação, preciso construir uma API capaz de rotear mensagens e arquivos por diversas plataformas (whatsapp, telegram, instagram directe e etc) e entre clientes internos (web, mobile, CLI). Ela deve suportar comunicação em grupo, privada, deve existir persistencia nas mensagens, controle de envio, recebimento e leitura, deve suportar entregas de arquivos de até 2gb e operação em escala de milhões de usuários."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Send & Receive Cross-Platform Messages (Priority: P1)

As an internal user (Web/Mobile/CLI), I want to exchange text messages with users on external platforms (WhatsApp, Telegram, Instagram) so that I can communicate without leaving my internal application.

**Why this priority**: This is the core value proposition of the "Universal Message Router". Without this, the system does not fulfill its primary purpose.

**Independent Test**: Can be tested by mocking an external provider (e.g., a mock Telegram server) and verifying that a message sent from the CLI reaches the mock server, and a message from the mock server reaches the CLI.

**Acceptance Scenarios**:

1. **Given** a registered internal user and a valid external contact (e.g., Telegram ID), **When** the internal user sends a text message, **Then** the system routes it to the correct external platform adapter and confirms submission.
2. **Given** an incoming webhook from an external platform (e.g., WhatsApp), **When** the system receives the payload, **Then** it identifies the target internal user and delivers the message to their active session.

---

### User Story 2 - Large File Transfer (Priority: P2)

As a user, I want to send and receive files up to 2GB across supported platforms so that I can share high-quality media and documents.

**Why this priority**: Handling large files imposes significant architectural constraints (streaming, storage) that need to be addressed early to ensure scalability.

**Independent Test**: Can be tested by uploading a 1.9GB dummy file via the API and verifying it is stored correctly and a download link/reference is generated.

**Acceptance Scenarios**:

1. **Given** a 2GB video file, **When** a user initiates an upload, **Then** the system accepts the stream without buffering the entire file in memory and stores it securely.
2. **Given** a stored file, **When** a recipient requests it, **Then** the system provides a secure method to download or stream the content.

---

### User Story 3 - Group Communication (Priority: P2)

As a user, I want to create groups with participants from different platforms so that we can collaborate in a single context.

**Why this priority**: Extends the core messaging capability to multi-user contexts, adding complexity to routing and state management.

**Independent Test**: Create a group entity in the database and verify that a message sent to the group ID is fanned out to all members.

**Acceptance Scenarios**:

1. **Given** a group with 1 internal user and 2 external users (WhatsApp, Telegram), **When** a message is sent to the group, **Then** all 3 participants receive the message.
2. **Given** a group, **When** a user is added or removed, **Then** the group membership is updated and system notifications are sent.

---

### User Story 4 - Message Reliability & Status (Priority: P3)

As a sender, I want to know if my message was sent, delivered, and read, so that I can be sure of communication.

**Why this priority**: Critical for user trust but can be implemented after the core routing logic is stable.

**Independent Test**: Simulate status updates from an external provider and verify the internal message state transitions.

**Acceptance Scenarios**:

1. **Given** a sent message, **When** the external platform confirms delivery, **Then** the message status updates to "Delivered".
2. **Given** a delivered message, **When** the recipient opens it (and the platform supports it), **Then** the message status updates to "Read".

### Edge Cases

- What happens when an external platform is down? (System should queue messages and retry).
- How does the system handle unsupported file types for specific platforms? (Should reject or convert if possible, but rejection is safer MVP).
- What happens if a user blocks the bot on the external platform? (System should handle delivery failures gracefully).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a unified **REST/gRPC** API to send messages to supported providers (WhatsApp, Telegram, Instagram, Internal).
- **FR-002**: System MUST ingest incoming messages from external platforms via webhooks or polling and route them to internal users.
- **FR-003**: System MUST persist all message history, metadata, and status changes in a durable **MongoDB** database.
- **FR-004**: System MUST support file uploads and downloads up to 2GB size limit using **S3-compatible object storage**.
- **FR-005**: System MUST implement an Adapter Pattern to allow adding new platforms without modifying core logic.
- **FR-006**: System MUST support creation and management of Group conversations with mixed platform participants.
- **FR-007**: System MUST track and expose message states: `pending`, `sent`, `delivered`, `read`, `failed`.
- **FR-008**: System MUST authenticate internal clients via **JWT (JSON Web Tokens)**.
- **FR-009**: System MUST use **Apache Kafka** to queue and route messages for delivery to handle spikes and platform outages (Asynchronous processing).

### Assumptions

- External platforms provide accessible APIs or Webhooks.
- Storage infrastructure is capable of handling 2GB files (e.g., S3-compatible).
- Internal clients are responsible for their own UI implementation.

### Key Entities *(include if feature involves data)*

- **User**: Represents an identity (Internal or External). Attributes: `id`, `platform`, `platform_id`, `display_name`.
- **Conversation**: A context for messages (Private or Group). Attributes: `id`, `type`, `participants`.
- **Message**: The content exchanged. Attributes: `id`, `conversation_id`, `sender_id`, `content`, `timestamp`, `status`.
- **Attachment**: File metadata. Attributes: `id`, `message_id`, `url`, `size`, `mime_type`.
- **Provider**: Configuration for an external platform. Attributes: `name`, `api_credentials`, `webhook_url`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: System successfully processes a 2GB file upload and download without memory overflow errors.
- **SC-002**: Message routing latency (internal ingress to external egress) is under 500ms for 95% of text messages (excluding external provider latency).
- **SC-003**: System handles a simulated load of 10,000 concurrent connections on a single node (proof of scalability architecture).
- **SC-004**: 100% of messages acknowledged by the API are persisted to storage (Zero data loss).
- **SC-005**: Adding a mock provider requires changes only to the adapter configuration, not the core engine.

## Clarifications

### Session 2025-11-23

- Q: Real-time delivery mechanism? → A: Kafka (Core message bus for routing and delivery).
- Q: Database strategy for message persistence? → A: NoSQL (MongoDB).
- Q: Large file storage strategy? → A: S3-Compatible Object Storage (MinIO/AWS).
- Q: Implementation language/framework? → A: Python (FastAPI).
- Q: Client-Server communication protocol? → A: REST/gRPC.

## Governance
