from datetime import datetime

from backend.api._base import ProjectResponse


class ProjectLike:
    id = "proj-1"
    name = "example"
    description = "desc"
    created_at = datetime.utcnow()
    updated_at = None


def test_project_response_supports_attribute_objects():
    parsed = ProjectResponse.model_validate(ProjectLike())
    assert parsed.id == "proj-1"
    assert parsed.name == "example"
