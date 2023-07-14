from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from celery import Celery
from pymongo import MongoClient
import uuid
import json
import time
import random
from typing import Optional
from bson import ObjectId


app = FastAPI()

client = MongoClient("mongodb://mongodb:27017/")

db = client["mydatabase"]
jobs_collection = db["jobs"]


celery_app = Celery(
    "job_queue",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/0"
)


class Job(BaseModel):
    id: str
    name: str
    model: str
    key: Optional[str] = None
    data_file: Optional[str] = None
    out_file: Optional[str] = None
    status: str


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        return super().default(obj)

def serialize_job(job_dict: dict):
    return {
        "id": job_dict["id"],
        "name": job_dict["name"],
        "model": job_dict["model"],
        "key": job_dict["key"],
        "data_file": job_dict["data_file"],
        "out_file": job_dict["out_file"],
        "status": job_dict["status"],
    }

@celery_app.task(bind=True)
def process_job(self, job_id):
    backend = 'redis://my-redis-container:6379/0'
    job = jobs_collection.find_one({"id": job_id})
    if job is None:
        raise ValueError(f"Job with ID {job_id} not found.")

    # Perform the necessary tasks to evaluate the model and generate the score
    score = evaluate_model(job)

    # Store the score in a JSON file
    score_file_path = f"score_{job_id}.json"
    with open(score_file_path, "w") as score_file:
        json.dump(score, score_file)

    # Update the job status to "Completed"
    jobs_collection.update_one({"id": job_id}, {"$set": {"status": "Completed"}})


@app.post("/jobs")
def create_job(job_data: dict):
    job_id = str(uuid.uuid4())

    job = Job(
        id=job_id,
        name=job_data["name"],
        model=job_data["model"],
        status="Pending"
    )

    job_dict = job.dict()

    jobs_collection.insert_one(job_dict)

    process_job.delay(job_id)

    return job_id

@app.put("/jobs/{job_id}/stop")
def stop_job(job_id: str):
    job = jobs_collection.find_one({"id": job_id})
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    if job["status"] != "Pending":
        raise HTTPException(status_code=400, detail="Only pending jobs can be stopped")

    # TODO: Stop the worker, remove from queue

    jobs_collection.update_one({"id": job_id}, {"$set": {"status": "Stopped"}})

    return {"message": "Job stopped successfully"}


@app.get("/jobs/{job_id}")
def describe_job(job_id: str):
    job = jobs_collection.find_one({"id": job_id})
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    job = serialize_job(job)

    return job


@app.get("/jobs")
@app.get("/jobs")
def list_jobs():
    job_records = jobs_collection.find()
    jobs = [serialize_job(job) for job in job_records]
    return jobs

#def list_jobs():
#    job_records = jobs_collection.find()
#    jobs = []
#    for job in job_records:
#        job_dict = {
#            "id": str(job["_id"]),
#            "name": job["name"],
#            "model": job["model"],
#            "key": job["key"],
#            "data_file": job["data_file"],
#            "out_file": job["out_file"],
#            "status": job["status"],
#        }
#        jobs.append(job_dict)
#    return jobs

def evaluate_model(job):
    time.sleep(random.randint(1, 5))
    return {"score": 0.8}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, json_serializer=CustomJSONEncoder().encode)

