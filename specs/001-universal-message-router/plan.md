# Implementation Plan: Universal Message Router

**Branch**: `001-universal-message-router` | **Date**: 2025-11-23 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-universal-message-router/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Build a scalable API to route messages and large files (up to 2GB) between internal clients (Web/Mobile/CLI) and external platforms (WhatsApp, Telegram, etc.). The system uses **Kafka** for asynchronous message routing, **MongoDB** for high-throughput persistence, and **S3-compatible storage** for files, implemented in **Python (FastAPI)**.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: FastAPI (API), aiokafka (Kafka), motor (MongoDB), boto3 (S3), grpcio (gRPC)
**Storage**: MongoDB (Messages/Metadata), MinIO/S3 (Files)
**Testing**: pytest, testcontainers (Integration)
**Target Platform**: Linux Containers (Docker/Kubernetes)
**Project Type**: Backend API
**Performance Goals**: <500ms routing latency (p95), support 2GB file streams
**Constraints**: Horizontal scalability, Asynchronous I/O, Stateless API nodes
**Scale/Scope**: Millions of users, High write throughput

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Scalability First**: PASSED. Architecture uses Kafka for decoupling and S3 for large files.
- **II. Universal Routing**: PASSED. Adapter pattern explicitly required for platform integrations.
- **III. Reliability & Persistence**: PASSED. MongoDB for persistence, Kafka for delivery guarantees.
- **IV. Secure & Private**: PASSED. JWT authentication and access controls defined.
- **V. Observability & Control**: PASSED. Metrics and health checks will be standard.

## Project Structure

### Documentation (this feature)

```text
specs/001-universal-message-router/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
src/
├── api/                 # Entry points (REST/gRPC)
│   ├── v1/              # REST Endpoints
│   └── grpc/            # gRPC Services
├── core/                # Configuration, Security, Logging
├── domain/              # Business Entities & Interfaces (Ports)
├── services/            # Application Logic (Router, FileService)
├── adapters/            # Infrastructure Implementations
│   ├── db/              # MongoDB Repositories
│   ├── storage/         # S3/MinIO Client
│   ├── messaging/       # Kafka Producer/Consumer
│   └── platforms/       # External Providers (Telegram, WhatsApp)
└── main.py              # Application Entrypoint

tests/
├── unit/                # Domain logic tests
├── integration/         # Adapter & Service tests (with Testcontainers)
└── e2e/                 # Full flow tests
```

**Structure Decision**: Hexagonal/Clean Architecture to isolate core routing logic from external platform adapters and infrastructure.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | | |
