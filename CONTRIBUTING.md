# Contributing to StateSet Data Studio

Thank you for your interest in contributing to StateSet Data Studio! This document provides guidelines and information for contributors.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How to Contribute](#how-to-contribute)
- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Submitting Changes](#submitting-changes)
- [Reporting Issues](#reporting-issues)
- [Testing](#testing)

## Code of Conduct

This project follows a code of conduct to ensure a welcoming environment for all contributors. Please read our [Code of Conduct](CODE_OF_CONDUCT.md) before contributing.

## How to Contribute

We welcome contributions in several forms:

- **Bug reports and feature requests** via GitHub Issues
- **Code contributions** via Pull Requests
- **Documentation improvements**
- **Testing and feedback**

### Types of Contributions

1. **Bug Fixes**: Fix existing issues
2. **Features**: Add new functionality
3. **Documentation**: Improve docs, add examples
4. **Tests**: Add or improve test coverage
5. **UI/UX**: Frontend improvements

## Development Setup

### Prerequisites

- Python 3.10+
- Node.js 16+
- Docker (optional)

### 1. Clone the Repository

```bash
git clone https://github.com/stateset/stateset-data-studio.git
cd synthetic-data-studio
```

### 2. Backend Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env with your API keys
```

### 3. Frontend Setup

```bash
cd frontend
npm install
cp .env.example .env
# Configure frontend environment variables
```

### 4. Database Setup

```bash
# Initialize database
python -c "from backend.db.session import init_db; init_db()"
```

## Project Structure

```
synthetic-data-studio/
├── backend/                 # FastAPI backend
│   ├── api/                # API endpoints
│   ├── services/           # Business logic
│   ├── db/                 # Database models and session
│   └── configs/            # Configuration files
├── frontend/               # React frontend
│   ├── src/
│   ├── public/
│   └── package.json
├── synthetic_data_kit/     # Core synthetic data generation
├── tests/                  # Test suite
├── examples/               # Example scripts
├── data/                   # Data directory structure
└── configs/                # Configuration files
```

## Submitting Changes

### 1. Fork and Branch

```bash
# Fork the repository on GitHub
# Clone your fork
git clone https://github.com/stateset/stateset-data-studio.git
cd stateset-data-studio

# Create a feature branch
git checkout -b feature/your-feature-name
```

### 2. Make Changes

- Write clear, concise commit messages
- Follow the existing code style
- Add tests for new functionality
- Update documentation as needed

### 3. Test Your Changes

```bash
# Run backend tests
cd backend
python -m pytest ../tests/

# Run frontend tests
cd frontend
npm test

# Manual testing
python run.py  # Start the application
```

### 4. Submit Pull Request

1. Push your changes to your fork
2. Create a Pull Request on GitHub
3. Fill out the PR template completely
4. Wait for review and address any feedback

## Pull Request Guidelines

- **Title**: Use clear, descriptive titles
- **Description**: Explain what and why, not just how
- **Commits**: Squash related commits
- **Tests**: Include tests for new features
- **Documentation**: Update docs for API changes

## Reporting Issues

### Bug Reports

When reporting bugs, please include:

- **Expected behavior**
- **Actual behavior**
- **Steps to reproduce**
- **Environment details** (OS, Python/Node versions)
- **Error messages/logs**

### Feature Requests

For feature requests, please include:

- **Use case**: Why do you need this feature?
- **Proposed solution**: How should it work?
- **Alternatives**: Other approaches considered?

## Testing

### Running Tests

```bash
# Backend tests
python -m pytest tests/ -v

# Frontend tests
cd frontend && npm test

# Integration tests
python run_api_tests.py
```

### Writing Tests

- Place tests in the `tests/` directory
- Use descriptive test names
- Test both success and failure cases
- Mock external dependencies

## Commit Message Guidelines

Format: `type(scope): description`

Types:
- `feat`: New features
- `fix`: Bug fixes
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Test additions/changes
- `chore`: Maintenance tasks

Example: `feat(auth): add OAuth2 login support`

## Questions?

Feel free to open a GitHub Discussion or contact the maintainers if you have questions about contributing.
