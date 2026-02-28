import json
import uuid
from pathlib import Path

import httpx
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app import app
from backend.db.models import Job
from backend.db.session import Base, get_db
from backend.settings import settings


@pytest.fixture()
def anyio_backend():
    return "asyncio"


@pytest.fixture()
async def api_context(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_file = tmp_path / "test.db"
    engine = create_engine(
        f"sqlite:///{db_file}",
        connect_args={"check_same_thread": False},
    )
    testing_session_local = sessionmaker(
        autocommit=False, autoflush=False, bind=engine
    )
    Base.metadata.create_all(bind=engine)

    data_dir = tmp_path / "data"
    backend_dir = tmp_path / "backend"
    data_dir.mkdir(parents=True, exist_ok=True)
    backend_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(settings, "project_root", tmp_path)
    monkeypatch.setattr(settings, "backend_dir", backend_dir)
    monkeypatch.setattr(settings, "data_dir", data_dir)
    monkeypatch.setattr("backend.services.jobs.SDKService.run", lambda *args, **kwargs: None)

    def override_get_db():
        db = testing_session_local()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as client:
        yield {
            "client": client,
            "session_local": testing_session_local,
            "data_dir": data_dir,
        }

    app.dependency_overrides.clear()
    engine.dispose()


async def _create_project(client: httpx.AsyncClient) -> str:
    response = await client.post(
        "/projects",
        json={"name": "test-project", "description": "integration test"},
    )
    assert response.status_code == 201
    return response.json()["id"]


@pytest.mark.anyio
async def test_projects_crud(api_context):
    client = api_context["client"]

    project_id = await _create_project(client)

    listed = await client.get("/projects")
    assert listed.status_code == 200
    assert any(item["id"] == project_id for item in listed.json())

    fetched = await client.get(f"/projects/{project_id}")
    assert fetched.status_code == 200
    assert fetched.json()["id"] == project_id

    deleted = await client.delete(f"/projects/{project_id}")
    assert deleted.status_code == 204

    missing = await client.get(f"/projects/{project_id}")
    assert missing.status_code == 404


@pytest.mark.anyio
async def test_jobs_ingest_create_and_download_flow(api_context):
    client = api_context["client"]
    session_local = api_context["session_local"]

    project_id = await _create_project(client)

    ingest = await client.post(
        "/jobs/ingest",
        data={"project_id": project_id},
        files={"file": ("sample.txt", b"hello world", "text/plain")},
    )
    assert ingest.status_code == 202
    ingest_job_id = ingest.json()["id"]

    ingest_job = await client.get(f"/jobs/{ingest_job_id}")
    assert ingest_job.status_code == 200
    ingest_output = Path(ingest_job.json()["output_file"])
    ingest_output.parent.mkdir(parents=True, exist_ok=True)
    ingest_output.write_text("processed text", encoding="utf-8")

    with session_local() as db:
        job = db.get(Job, ingest_job_id)
        job.status = "completed"
        db.commit()

    create = await client.post(
        "/jobs/create",
        data={
            "project_id": project_id,
            "input_file": str(ingest_output),
            "qa_type": "qa",
            "num_pairs": "2",
        },
    )
    assert create.status_code == 202
    create_job_id = create.json()["id"]

    with session_local() as db:
        created_job = db.get(Job, create_job_id)
        output_path = Path(created_job.output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps({"qa_pairs": [{"question": "q1", "answer": "a1"}]}),
            encoding="utf-8",
        )
        created_job.status = "completed"
        created_job.error = None
        db.commit()

    download = await client.get(f"/jobs/{create_job_id}/download")
    assert download.status_code == 200
    payload = download.json()
    assert "filename" in payload
    assert "content" in payload


@pytest.mark.anyio
async def test_jobs_reject_path_traversal(api_context):
    client = api_context["client"]
    project_id = await _create_project(client)

    response = await client.post(
        "/jobs/create",
        data={
            "project_id": project_id,
            "input_file": "/etc/passwd",
            "qa_type": "qa",
        },
    )
    assert response.status_code == 400
    assert "within data directories" in response.json()["detail"]


@pytest.mark.anyio
async def test_ingest_rejects_unsupported_extension(api_context):
    client = api_context["client"]
    project_id = await _create_project(client)

    response = await client.post(
        "/jobs/ingest",
        data={"project_id": project_id},
        files={"file": ("payload.exe", b"MZ...", "application/octet-stream")},
    )
    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]


@pytest.mark.anyio
async def test_restart_stalled_jobs_requeues_supported_jobs(api_context):
    client = api_context["client"]
    session_local = api_context["session_local"]
    data_dir = api_context["data_dir"]

    project_id = await _create_project(client)
    input_file = data_dir / "output" / "restart_source.txt"
    input_file.parent.mkdir(parents=True, exist_ok=True)
    input_file.write_text("restart source", encoding="utf-8")

    stalled_job_id = str(uuid.uuid4())
    with session_local() as db:
        stalled = Job(
            id=stalled_job_id,
            project_id=project_id,
            job_type="create",
            status="running",
            input_file=str(input_file),
            output_file=str(data_dir / "generated" / "stalled.json"),
            config=json.dumps({"qa_type": "qa", "num_pairs": 1}),
        )
        db.add(stalled)
        db.commit()

    response = await client.post("/system/restart-stalled-jobs")
    assert response.status_code == 200
    body = response.json()
    assert body["restarted"] == 1
    assert body["jobs"][0]["old_job_id"] == stalled_job_id

    with session_local() as db:
        old_job = db.get(Job, stalled_job_id)
        assert old_job.status == "failed"
        assert "Restarted by /system/restart-stalled-jobs" in (old_job.error or "")

        project_jobs = db.query(Job).filter(Job.project_id == project_id).all()
        assert len(project_jobs) == 2


@pytest.mark.anyio
async def test_jobs_list_supports_status_and_status_param(api_context):
    client = api_context["client"]
    session_local = api_context["session_local"]
    data_dir = api_context["data_dir"]

    project_id = await _create_project(client)
    input_file = data_dir / "output" / "list_filter_source.txt"
    input_file.parent.mkdir(parents=True, exist_ok=True)
    input_file.write_text("filter source", encoding="utf-8")

    create_resp = await client.post(
        "/jobs/create",
        data={
            "project_id": project_id,
            "input_file": str(input_file),
            "qa_type": "qa",
            "num_pairs": "1",
        },
    )
    assert create_resp.status_code == 202
    job_id = create_resp.json()["id"]

    with session_local() as db:
        job = db.get(Job, job_id)
        job.status = "completed"
        db.commit()

    by_status = await client.get("/jobs", params={"project_id": project_id, "status": "completed"})
    assert by_status.status_code == 200
    assert len(by_status.json()) == 1
    assert by_status.json()[0]["id"] == job_id

    by_status_param = await client.get(
        "/jobs",
        params={"project_id": project_id, "status_param": "completed"},
    )
    assert by_status_param.status_code == 200
    assert len(by_status_param.json()) == 1
    assert by_status_param.json()[0]["id"] == job_id


@pytest.mark.anyio
async def test_extensions_process_file_creates_ingest_job(api_context):
    client = api_context["client"]
    project_id = await _create_project(client)

    response = await client.post(
        "/extensions/process-file",
        data={"project_id": project_id},
        files={"file": ("from_extension.txt", b"extension upload", "text/plain")},
    )
    assert response.status_code == 202
    payload = response.json()
    assert payload["job_type"] == "ingest"
    assert payload["status"] in {"pending", "running"}


@pytest.mark.anyio
async def test_restart_stalled_jobs_skips_unsupported_type(api_context):
    client = api_context["client"]
    session_local = api_context["session_local"]
    project_id = await _create_project(client)

    bad_job_id = str(uuid.uuid4())
    with session_local() as db:
        bad = Job(
            id=bad_job_id,
            project_id=project_id,
            job_type="mystery",
            status="running",
            input_file="data/output/unknown.txt",
            output_file=None,
            config=json.dumps({}),
        )
        db.add(bad)
        db.commit()

    response = await client.post("/system/restart-stalled-jobs")
    assert response.status_code == 200
    payload = response.json()
    assert payload["restarted"] == 0
    assert len(payload["skipped"]) == 1
    assert payload["skipped"][0]["job_id"] == bad_job_id

    with session_local() as db:
        bad = db.get(Job, bad_job_id)
        assert bad.status == "failed"
        assert "Restart skipped" in (bad.error or "")
