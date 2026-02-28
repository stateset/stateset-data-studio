# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.1.0] - 2026-02-28

### Added
- Deterministic backend API integration tests for projects, jobs, security checks, and stalled-job recovery.
- Frontend test scaffolding and baseline UI smoke test.
- Compatibility shim for legacy `backend.api_extensions` imports.

### Changed
- Unified and hardened file path handling to restrict file operations to allowed data roots.
- Sanitized upload filename handling and rejected unsupported uploaded file types.
- Simplified frontend API client to canonical backend endpoints and removed host-specific fallback logic.
- Updated CI to include backend import smoke tests, frontend linting, and stronger docker image validation.
- Updated release metadata to `1.1.0` across backend/frontend/runtime manifests.

### Fixed
- Fixed route decorator annotation/signature handling that could break FastAPI startup.
- Fixed `/system/restart-stalled-jobs` to correctly requeue supported jobs and report skipped cases.
- Fixed ORM response serialization for project responses.
- Fixed SDK task error handling so unexpected subprocess failures are persisted as failed jobs.

### Security
- Removed path traversal vectors from file-based job endpoints.
- Enforced blocking backend Bandit checks in CI.

### Features
- **Data Ingestion**: Upload documents or provide URLs for processing
- **QA Generation**: Generate question-answer pairs from text content
- **Chain of Thought**: Create reasoning examples with step-by-step solutions
- **Quality Curation**: Filter and rate generated content based on quality thresholds
- **Export Options**: Save data in various formats for fine-tuning
- **Project Management**: Organize work into separate projects
- **Real-time Monitoring**: Track job progress and system status

### Technical
- Python 3.10+ backend with FastAPI
- React frontend with modern UI components
- SQLite database for job and project management
- Comprehensive logging and error handling
- RESTful API with OpenAPI documentation
- MCP server for programmatic access

## [1.0.0] - 2024-12-XX

### Added
- Complete synthetic data generation pipeline
- Multi-format document processing
- Quality assessment and curation system
- Multiple LLM provider support
- Export to fine-tuning formats
- Docker deployment support
- Comprehensive documentation

### Security
- Environment variable configuration
- Input validation and sanitization
- Secure API key handling
- No persistent data storage by default

### Documentation
- Complete setup and usage guide
- API documentation
- MCP server documentation
- Contributing guidelines
- Security policy
- Code of conduct

---

## Types of Changes
- `Added` for new features
- `Changed` for changes in existing functionality
- `Deprecated` for soon-to-be removed features
- `Removed` for now removed features
- `Fixed` for any bug fixes
- `Security` in case of vulnerabilities

## Versioning
This project uses [Semantic Versioning](https://semver.org/).

Given a version number MAJOR.MINOR.PATCH, increment the:

- **MAJOR** version when you make incompatible API changes
- **MINOR** version when you add functionality in a backwards compatible manner
- **PATCH** version when you make backwards compatible bug fixes

---

[Unreleased]: https://github.com/stateset/stateset-data-studio/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/stateset/stateset-data-studio/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/stateset/stateset-data-studio/releases/tag/v1.0.0
