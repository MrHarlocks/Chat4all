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

## Phase 4: User Story 2 - Large File Transfer (Priority: P2)

**Goal**: Enable upload and download of large files (up to 2GB) via S3-compatible storage.

**Independent Test**: Verify file upload URL generation and successful file metadata storage.

### Tests for User Story 2

- [x] T023 [P] [US2] Create integration test for file upload URL generation in `tests/integration/test_files.py`

### Implementation for User Story 2

- [x] T024 [P] [US2] Update `Attachment` model in `src/domain/models.py` (if needed)
- [x] T025 [US2] Implement `FileService` for presigned URL generation in `src/services/file_service.py`
- [x] T026 [US2] Implement `POST /files/upload-url` endpoint in `src/api/v1/endpoints/files.py`
- [x] T027 [US2] Update `MessageService` to handle messages with attachments in `src/services/message_service.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Group Communication (Priority: P2)

**Goal**: Enable creation and management of group conversations.

**Independent Test**: Verify group creation and message fan-out to participants.

### Tests for User Story 3

- [x] T028 [P] [US3] Create integration test for group creation in `tests/integration/test_groups.py`

### Implementation for User Story 3

- [x] T029 [P] [US3] Implement `ConversationRepository` in `src/adapters/db/conversation_repository.py`
- [x] T030 [US3] Implement `ConversationService` in `src/services/conversation_service.py`
- [x] T031 [US3] Implement `POST /conversations` endpoint in `src/api/v1/endpoints/conversations.py`
- [x] T032 [US3] Update `RouterService` to handle group message fan-out in `src/services/router_service.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: User Story 4 - Message Reliability & Status (Priority: P3)

**Goal**: Track and expose message delivery status (Sent, Delivered, Read).

**Independent Test**: Verify status updates propagate from provider to database.

### Tests for User Story 4

- [x] T033 [P] [US4] Create integration test for status updates in `tests/integration/test_status.py`

### Implementation for User Story 4

- [x] T034 [US4] Update `MessageRepository` to support status updates in `src/adapters/db/message_repository.py`
- [x] T035 [US4] Implement status update consumer logic in `src/services/router_service.py`
- [x] T036 [US4] Implement `GET /messages/{messageId}` endpoint in `src/api/v1/endpoints/messages.py`

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T037 [P] Update API documentation (Swagger UI) description in `src/main.py`
- [x] T038 Implement structured logging middleware in `src/core/middleware.py`
- [x] T039 [P] Add health check endpoint in `src/api/health.py`
- [x] T040 Run quickstart.md validation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable
- **User Story 4 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 for message existence

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Create integration test for message sending flow in tests/integration/test_send_message.py"
Task: "Create integration test for webhook ingestion flow in tests/integration/test_webhook.py"

# Launch all adapters for User Story 1 together:
Task: "Define MessageProvider interface in src/domain/interfaces/provider.py"
Task: "Implement MockProvider for testing in src/adapters/platforms/mock_provider.py"
Task: "Implement MessageRepository for MongoDB operations in src/adapters/db/message_repository.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1
   - Developer B: User Story 2
   - Developer C: User Story 3
3. Stories complete and integrate independently
