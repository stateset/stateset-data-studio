from fastapi import Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.api._base import BaseRouter, ProjectResponse
from backend.services.projects import ProjectService
from backend.db.session import get_db

router = BaseRouter(prefix="/projects", tags=["Projects"])

class ProjectIn(BaseModel):
    name: str
    description: str | None = None

@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(body: ProjectIn, db: Session = Depends(get_db)):
    return ProjectService.create(db, **body.dict())

@router.get("", response_model=list[ProjectResponse])
def list_projects(db: Session = Depends(get_db)):
    return ProjectService.list(db)

@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: str, db: Session = Depends(get_db)):
    proj = ProjectService.get(db, project_id)
    if not proj:
        raise HTTPException(404, "Project not found")
    return proj

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: str, db: Session = Depends(get_db)):
    if not ProjectService.delete(db, project_id):
        raise HTTPException(404, "Project not found")