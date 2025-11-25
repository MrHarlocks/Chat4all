---
description: "Task list for Universal Message Router implementation"
---

# Tasks: Universal Message Router

**Input**: Design documents from `/specs/001-universal-message-router/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/openapi.yaml

**Tests**: Integration tests are included to verify independent user stories as per specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Project Root**: `src/`
- **Tests**: `tests/`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Create project structure per implementation plan
- [x] T002 Initialize Python project with FastAPI, Motor, AIOKafka, Boto3 dependencies in `requirements.txt`
- [x] T003 [P] Create Docker Compose configuration for Kafka, MongoDB, and MinIO in `docker-compose.yml`
- [x] T004 [P] Configure linting and formatting tools (ruff/black) in `pyproject.toml`
- [x] T005 Create main application entrypoint in `src/main.py`
- [x] T006 Create configuration management module in `src/core/config.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T007 Setup MongoDB connection and database client in `src/adapters/db/mongo_client.py`
- [x] T008 [P] Setup Kafka producer and consumer clients in `src/adapters/messaging/kafka_client.py`
- [x] T009 [P] Setup S3/MinIO client in `src/adapters/storage/s3_client.py`
- [x] T010 [P] Create base Pydantic models for entities in `src/domain/models.py`
- [x] T011 Configure logging infrastructure in `src/core/logging.py`
- [x] T012 Setup global exception handlers in `src/core/exceptions.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Send & Receive Cross-Platform Messages (Priority: P1) 🎯 MVP

**Goal**: Enable internal users to exchange text messages with external platforms via a unified API.

**Independent Test**: Verify message flow from API -> Kafka -> Mock Provider and Webhook -> Kafka -> API.

### Tests for User Story 1

- [x] T013 [P] [US1] Create integration test for message sending flow in `tests/integration/test_send_message.py`
- [x] T014 [P] [US1] Create integration test for webhook ingestion flow in `tests/integration/test_webhook.py`

### Implementation for User Story 1

- [x] T015 [P] [US1] Define `MessageProvider` interface in `src/domain/interfaces/provider.py`
- [x] T016 [P] [US1] Implement `MockProvider` for testing in `src/adapters/platforms/mock_provider.py`
- [x] T017 [US1] Implement `MessageRepository` for MongoDB operations in `src/adapters/db/message_repository.py`
- [x] T018 [US1] Implement `MessageService` (send logic) in `src/services/message_service.py`
- [x] T019 [US1] Implement `RouterService` (consume & route logic) in `src/services/router_service.py`
- [x] T020 [US1] Implement `POST /messages` endpoint in `src/api/v1/endpoints/messages.py`
- [x] T021 [US1] Implement Webhook ingress endpoint in `src/api/v1/endpoints/webhooks.py`
- [x] T022 [US1] Register message routes in `src/api/v1/router.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Advanced File Handling (Priority: P2)

**Goal**: Enable upload and download of large files (up to 2GB) via S3-compatible storage with metadata tracking.

**Independent Test**: Verify file upload URL generation, metadata storage, and download URL generation.

### Tests for User Story 2

- [x] T023 [P] [US2] Create integration test for file upload URL generation in `tests/integration/test_files.py`

### Implementation for User Story 2

- [x] T024 [P] [US2] Update `Attachment` model in `src/domain/models.py` to include `checksum`, `uploader_id`, `file_id`
- [x] T025 [US2] Implement `FileRepository` in `src/adapters/db/file_repository.py` to store file metadata
- [x] T026 [US2] Update `FileService` to store metadata and support `generate_download_url` in `src/services/file_service.py`
- [x] T027 [US2] Update `POST /files/upload-url` to accept metadata and register file in DB
- [x] T028 [US2] Implement `GET /files/{file_id}/download-url` endpoint in `src/api/v1/endpoints/files.py`
- [x] T029 [US2] Update `MessageService` to validate `file_id` when sending messages with type "file"

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Group Communication (Priority: P2)

**Goal**: Enable creation and management of group conversations.

**Independent Test**: Verify group creation and message fan-out to participants.

### Tests for User Story 3

- [x] T030 [P] [US3] Create integration test for group creation in `tests/integration/test_groups.py`

### Implementation for User Story 3

- [x] T031 [P] [US3] Implement `ConversationRepository` in `src/adapters/db/conversation_repository.py`
- [x] T032 [US3] Implement `ConversationService` in `src/services/conversation_service.py`
- [x] T033 [US3] Implement `POST /conversations` endpoint in `src/api/v1/endpoints/conversations.py`
- [x] T034 [US3] Update `RouterService` to handle group message fan-out in `src/services/router_service.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Mock Connectors & Status Simulation (Priority: P3)

**Goal**: Create specific mock connectors for WhatsApp and Instagram that simulate real-world latency and status updates.

**Independent Test**: Verify status updates propagate from provider to database.

### Tests for User Story 4 & Connectors

- [x] T035 [P] [US4] Create integration test for status updates in `tests/integration/test_status.py`
- [x] T036 [P] [US4] Create integration test for full lifecycle (Send -> Mock -> Delivered -> Read)

### Implementation for Connectors & Status

- [x] T037 [US4] Create `WhatsAppMockConnector` service that consumes `whatsapp.outbound` topic
- [x] T038 [US4] Create `InstagramMockConnector` service that consumes `instagram.outbound` topic
- [x] T039 [US4] Implement simulation logic: Log receipt -> Wait -> Send DELIVERED callback -> Wait -> Send READ callback
- [x] T040 [US4] Update `RouterService` to route messages to specific topics (`whatsapp.outbound`, etc.) based on platform
- [x] T041 [US4] Implement `POST /webhooks/callbacks` or similar to receive status updates from mocks
- [ ] T042 [US4] Implement Websocket endpoint `ws://.../events` for real-time client notifications (Optional/Bonus)

---

## Phase 7: Polish & Documentation

**Purpose**: Improvements that affect multiple user stories

- [x] T043 [P] Update API documentation (Swagger UI) description in `src/main.py`
- [x] T044 Implement structured logging middleware in `src/core/middleware.py`
- [x] T045 [P] Add health check endpoint in `src/api/health.py`
- [x] T046 Update OpenAPI schema with new File and Status fields
- [x] T047 Update technical report with delivery flows

---
