from fastapi import BackgroundTasks
from sqlalchemy.orm import Session
from services.sdk import run_sdk

def enqueue_sdk(background: BackgroundTasks, job, command, args, db: Session):
    background.add_task(run_sdk, job, command, args, db)
