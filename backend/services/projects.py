from sqlalchemy.orm import Session
from backend.db.models import Project
import uuid

class ProjectService:
    @staticmethod
    def create(db: Session, name: str, description: str | None = None):
        proj = Project(id=str(uuid.uuid4()), name=name, description=description)
        db.add(proj); db.commit(); db.refresh(proj)
        return proj

    @staticmethod
    def list(db: Session):
        return db.query(Project).order_by(Project.created_at.desc()).all()

    @staticmethod
    def get(db: Session, project_id: str):
        return db.get(Project, project_id)

    @staticmethod
    def delete(db: Session, project_id: str):
        proj = ProjectService.get(db, project_id)
        if proj:
            db.delete(proj); db.commit()
        return proj