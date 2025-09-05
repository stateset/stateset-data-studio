# StateSet Data Studio

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Node.js 16+](https://img.shields.io/badge/node.js-16+-green.svg)](https://nodejs.org/)
[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=flat&logo=docker&logoColor=white)](https://docker.com/)
[![CI](https://github.com/stateset/stateset-data-studio/actions/workflows/ci.yml/badge.svg)](https://github.com/stateset/stateset-data-studio/actions/workflows/ci.yml)

A comprehensive web-based platform for generating high-quality synthetic datasets to fine-tune Large Language Models (LLMs). Built with FastAPI backend and React frontend, featuring AI agent integration via MCP server.

## ✨ Features

- **🎯 Multi-Format Support**: Process PDF, DOCX, TXT, HTML, and YouTube content
- **🤖 Multiple LLM Providers**: Support for Llama, OpenAI, and other providers
- **📊 Quality Curation**: AI-powered quality assessment and filtering
- **🔄 Export Formats**: JSONL, Alpaca, ChatML, OpenAI fine-tuning formats
- **🤖 AI Agent Integration**: MCP server for programmatic access
- **🐳 Docker Ready**: Containerized deployment with Docker Compose
- **📈 Real-time Monitoring**: Track job progress and system status
- **🎨 Modern UI**: Clean, responsive React interface

## 🚀 Quick Start

The easiest way to get started is using the provided run script:

```bash
# Clone the repository
git clone https://github.com/stateset/stateset-data-studio.git
cd synthetic-data-studio

# Make sure you have installed all dependencies first
python run.py
```

This will start:
- Backend API on http://localhost:8000
- Frontend UI on http://localhost:3000
- MCP Server on port 8000

## 📋 Prerequisites

- Python 3.10+
- Node.js 16+
- Docker (optional, for containerized deployment)
- Hugging Face account with API access
- LLM API access (Llama, OpenAI, etc.)

## 🛠️ Installation

### Option 1: Quick Setup (Recommended)

```bash
# Clone and setup
git clone https://github.com/stateset/stateset-data-studio.git
cd synthetic-data-studio

# Copy environment configuration
cp .env.example .env

# Edit .env with your API keys
nano .env

# Run the application
python run.py
```

### Option 2: Manual Setup

#### Backend Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt
```

#### Frontend Setup
```bash
cd frontend
npm install
npm start
```

## 🤖 AI Agent Integration

StateSet Data Studio includes an MCP (Model Control Protocol) server for AI agent integration:

```bash
# Start MCP server
python run_mcp_server.py
```

### Example Agent Usage
```python
# See examples/agent_example.py for complete integration
from mcp_client import MCPClient

client = MCPClient("http://localhost:8000")
# Create project, upload documents, generate data
```

## 📖 Usage Guide

### 1. System Configuration
1. Access the web interface at http://localhost:3000
2. Configure your LLM provider settings
3. Verify vLLM server connection

### 2. Create a Project
1. Click "New Project"
2. Enter project details
3. Start data generation workflow

### 3. Data Generation Workflow
1. **Ingest**: Upload documents or provide URLs
2. **Generate**: Create QA pairs or Chain of Thought examples
3. **Curate**: Filter content based on quality thresholds
4. **Export**: Save in your preferred format

## 🐳 Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d

# Or build manually
docker build -t synthetic-data-studio .
docker run -p 8000:8000 -p 3000:3000 synthetic-data-studio
```

## 🔧 Configuration

### Environment Variables

```bash
# Required
HF_TOKEN=your_hugging_face_token
LLAMA_API_KEY=your_llama_api_key
OPENAI_API_KEY=your_openai_api_key

# Optional
HOST=0.0.0.0
PORT=8000
DATABASE_URL=sqlite:///./synthetic_data.db
```

### Supported File Formats

- **Documents**: PDF, DOCX, TXT, HTML
- **Media**: YouTube URLs (video transcripts)
- **Archives**: ZIP files containing documents

## 📊 API Documentation

Once running, access the API documentation at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## 🧪 Testing

```bash
# Backend tests
python -m pytest tests/ -v

# Frontend tests
cd frontend && npm test

# Integration tests
python run_api_tests.py
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔒 Security

See our [Security Policy](SECURITY.md) for information about reporting vulnerabilities.

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/) and [React](https://reactjs.org/)
- LLM integration powered by [vLLM](https://vllm.ai/)
- UI components from [Tailwind CSS](https://tailwindcss.com/)

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/stateset/stateset-data-studio/issues)
- **Discussions**: [GitHub Discussions](https://github.com/stateset/stateset-data-studio/discussions)
- **Documentation**: [MCP Server Docs](MCP_SERVER_DOCS.md)

---

<p align="center">
  <strong>StateSet Data Studio</strong> - Transform documents into high-quality synthetic datasets
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#quick-start">Quick Start</a> •
  <a href="#contributing">Contributing</a> •
  <a href="#license">License</a>
</p>
