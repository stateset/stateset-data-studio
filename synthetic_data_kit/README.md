# Synthetic Data Kit

A toolkit for generating, processing, and curating synthetic data for AI training and evaluation.

## Overview

Synthetic Data Kit provides tools to:

1. Process and extract text from various document formats (PDF, DOCX, HTML, YouTube transcripts, etc.)
2. Generate high-quality question-answer pairs from text content
3. Create chain-of-thought reasoning examples for enhancing AI capabilities
4. Curate and filter synthetic data based on quality thresholds
5. Convert datasets to various formats for model fine-tuning

## Features

### Document Processing

- Parse text from PDF, DOCX, PPTX, HTML, TXT files
- Extract transcripts from YouTube videos
- Fetch and process HTML content from URLs

### Content Generation

- Generate question-answer pairs from document text
- Create chain-of-thought reasoning examples with step-by-step explanations
- Enhance existing conversations with chain-of-thought reasoning
- Generate summaries of documents

### Quality Control

- Rate and filter QA pairs based on quality thresholds
- Batch processing of content for efficiency
- Automatic fallback mechanisms for robust processing

### Format Conversion

- Convert datasets to JSONL, Alpaca, OpenAI fine-tuning, and ChatML formats
- Support for both file storage and Hugging Face datasets
- CSV export for tabular data applications

## Architecture

The toolkit is organized into several modules:

- **models**: LLM client for interacting with language models via vLLM API
- **generators**: Content generation tools for QA pairs and chain-of-thought examples
- **parsers**: File format parsers for different document types
- **utils**: Utility functions for configuration, text processing, and format conversion

## API Integration

The toolkit provides API extensions for the StateSet Data Studio backend, including:

- REST endpoints for file processing, QA generation, curation, and format conversion
- Background task processing for compute-intensive operations
- Job management and status tracking

## Configuration

Create a `config.yaml` file in the `configs` directory:

```yaml
vllm:
  api_base: "http://localhost:8000/v1"
  model: "meta-llama/Llama-3.1-70B-Instruct"
generation:
  temperature: 0.7
  chunk_size: 4000
  num_pairs: 25
curate:
  threshold: 7.0
  batch_size: 8
  temperature: 0.1
  inference_batch: 32
```

## Usage

The toolkit can be used directly in code:

```python
from synthetic_data_kit.models.llm_client import LLMClient
from synthetic_data_kit.generators.qa_generator import QAGenerator
from synthetic_data_kit.parsers.pdf_parser import PDFParser

# Initialize LLM client
client = LLMClient()

# Parse a PDF document
parser = PDFParser()
text = parser.parse("document.pdf")

# Generate QA pairs
generator = QAGenerator(client)
result = generator.process_document(text, num_pairs=10)

# Export to JSON
import json
with open("qa_pairs.json", "w") as f:
    json.dump(result, f, indent=2)
```

Or accessed through the REST API:

```bash
# Process a file
curl -X POST "http://localhost:8000/synthdata/process-file" \
  -H "Content-Type: application/json" \
  -d '{"file_path": "data/uploads/document.pdf", "output_dir": "data/output"}'

# Generate QA pairs
curl -X POST "http://localhost:8000/synthdata/create-qa" \
  -F "project_id=your-project-id" \
  -F "file_path=data/output/document.txt" \
  -F "content_type=qa" \
  -F "num_pairs=25"
```

## License

This project is licensed under the terms described in the LICENSE file in the root directory of this source tree.

## Acknowledgements

This toolkit builds upon concepts and approaches from Meta's synthetic data generation techniques as described in their research papers and open-source tools.