from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from celery import Celery
from celery.utils.log import get_task_logger
from pymongo import MongoClient
import uuid
import json
import time
import random
from typing import Optional
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient
import os
import subprocess


app = FastAPI()

client = MongoClient("mongodb://mongodb:27017/")

db = client["mydatabase"]
jobs_collection = db["jobs"]


celery_app = Celery(
    "job_queue",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/0"
)
logger = get_task_logger(__name__)


# Establishing async connection to MongoDB
async def get_db():
    client = AsyncIOMotorClient("mongodb://mongodb:27017/")
    db = client["mydatabase"]
    return db

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
    logger.info(f"Processing job with ID: {job_id}")
    backend = 'redis://my-redis-container:6379/0'
    job = jobs_collection.find_one({"id": job_id})
    if job is None:
        raise ValueError(f"Job with ID {job_id} not found.")

    # Perform the necessary tasks to evaluate the model and generate the score
    score = evaluate_model(job)

    jobs_collection.update_one({"id": job_id}, {"$set": {"status": "Completed", "out_file": score}})


@app.post("/jobs")
async def create_job(job_data: dict):
    job_id = str(uuid.uuid4())

    job = Job(
        id=job_id,
        name=job_data["name"],
        model=job_data["model"],
        status="Pending"
    )

    job_dict = job.dict()

    jobs_collection.insert_one(job_dict)

    task = process_job.delay(job_id)
    jobs_collection.update_one({"id": job_id}, {"$set": {"task_id": task.id}})

    return job_id

@app.put("/jobs/{job_id}/stop")
async def stop_job(job_id: str):
    job = jobs_collection.find_one({"id": job_id})
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    if job["status"] != "Pending":
        raise HTTPException(status_code=400, detail="Only pending jobs can be stopped")

    if "task_id" in job:
        revoke_task(job["task_id"])


    jobs_collection.update_one({"id": job_id}, {"$set": {"status": "Stopped"}})

    return {"message": "Job stopped successfully"}


@app.get("/jobs/{job_id}")
async def describe_job(job_id: str):
    job =  jobs_collection.find_one({"id": job_id})
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    job = serialize_job(job)

    return job


@app.get("/jobs")
async def list_jobs():
    job_records =  jobs_collection.find()
    jobs = [serialize_job(job) for job in job_records]
    return jobs


@app.delete("/jobs")
async def delete_all_jobs():
    # Retrieve all jobs
    job_records = jobs_collection.find({})
    job_ids = []
    task_ids = []

    for job in job_records:
        job_ids.append(job["id"])
        if "task_id" in job:
            task_ids.append(job["task_id"])

    # Revoke the tasks associated with the jobs
    for task_id in task_ids:
        revoke_task(task_id)

    # Delete all jobs
    result = jobs_collection.delete_many({})

    return {"message": f"Deleted {result.deleted_count} jobs."}


def evaluate_model(job):
    # job is a type of dict
    # Store the current directory
    current_dir = os.getcwd()
    print("Evalute Model " + str(job))
    try:
        # Change to the DecodingTrust directory
        os.chdir("DecodingTrust")

        # Execute the command
        command = [
            "python", 
            "adv-glue-plus-plus/gpt_eval.py",
            "--model",
            "gpt-3.5-turbo-0301",
            "--key",
            "test123",  # job.get('key', ''),  # Assumes job's 'key' parameter is the desired key
            "--data-file",
            "data/adv-glue-plus-plus/data/alpaca.json",  # Replace this with the desired data file path
            "--out-file",
            "data/test123"    # f"data/test_output_{job['id']}.json"  # Output file name includes job id
        ]
        subprocess.run(command, check=True)
        out_file = "data/test123"  #f"data/test_output_{job['id']}.json"

        # Read and return the results
        with open(out_file, "r") as f:
            results = json.load(f)
        return results

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        # Change back to the original directory
        os.chdir(current_dir)
    return {"score": random.randint(10, 15), "file":"s3//myS3bucket/"}
def revoke_task(task_id):
    celery_app.control.revoke(task_id, terminate=True)



if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, json_serializer=CustomJSONEncoder().encode)

