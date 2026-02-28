import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

collect_ignore = [
    "test_api_import.py",
    "test_complete_solution.py",
    "test_connection.py",
    "test_create_job.py",
    "test_curate.py",
    "test_file_paths.py",
    "test_jobs_curate.py",
    "test_llama_api.py",
    "test_normalize_path.py",
    "test_path_handling.py",
    "test_qa_fix.py",
    "test_qa_generation.py",
    "test_sdk.py",
    "test_workflow.py",
    "test_youtube_ingestion.py",
]
