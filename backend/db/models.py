from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from .session import Base, engine

class Project(Base):
    __tablename__ = "projects"

    id          = Column(String, primary_key=True)
    name        = Column(String, nullable=False)
    description = Column(String)
    created_at  = Column(DateTime, default=datetime.utcnow)
    updated_at  = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    jobs = relationship("Job", back_populates="project", cascade="all, delete-orphan")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Project {self.id!r} {self.name!r}>"


class Job(Base):
    __tablename__ = "jobs"

    id          = Column(String, primary_key=True)
    project_id  = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    job_type    = Column(String, nullable=False)          # ingest / create / curate / save-as
    status      = Column(String, default="pending")
    input_file  = Column(String)
    output_file = Column(String)
    config      = Column(Text)                            # JSON string
    stats       = Column(Text)
    error       = Column(Text)
    created_at  = Column(DateTime, default=datetime.utcnow)
    updated_at  = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("Project", back_populates="jobs")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Job {self.id!r} {self.job_type} {self.status}>"


# create tables on import (safe for SQLite / dev)
Base.metadata.create_all(bind=engine)
