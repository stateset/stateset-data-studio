# Data Directory Structure

This directory contains the data files used by the Synthetic Data Studio.

## Directory Structure

- `generated/` - Raw generated QA pairs and synthetic data
- `cleaned/` - Curated and filtered QA pairs after quality assessment
- `final/` - Final processed datasets ready for export and fine-tuning
- `uploads/` - Uploaded source documents (PDF, TXT, DOCX, etc.)
- `output/` - Processed text extracted from uploaded documents
- `txt/` - Text files extracted from various sources
- `pdf/` - PDF documents for processing
- `html/` - HTML content for processing
- `docx/` - Word documents for processing
- `ppt/` - PowerPoint presentations for processing
- `youtube/` - YouTube video transcripts

## File Formats

- **JSON**: QA pairs and metadata
- **JSONL**: Fine-tuning datasets compatible with OpenAI/Hugging Face
- **TXT**: Extracted text content
- **PDF/DOCX/PPT**: Source documents

## Sample Files

- `generated/sample_qa_pairs.json` - Example of generated QA pairs format

## Notes

- Generated data files are not included in version control
- Upload your own documents to the `uploads/` directory
- The application will automatically process and organize files
