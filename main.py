from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from celery import Celery
from pymongo import MongoClient
import uuid
import json
import time
import random

app = FastAPI()

client = MongoClient("mongodb://mongodb:27017/")  # Use the MongoDB service name as the hostname

# Get a reference to the database and collection
db = client["mydatabase"]
jobs_collection = db["jobs"]


# Create a Celery application
celery_app = Celery(
    "job_queue",
    broker="redis://redis:6379/0",  # Updated Redis URL
    backend="redis://redis:6379/0"  # Updated Redis URL
)

# Job model
class Job(BaseModel):
    id: str
    name: str
    status: str

# Create a task to process the job asynchronously
@celery_app.task(bind=True)
def process_job(self, job_id: str, job_data: dict):
    backend = 'redis://my-redis-container:6379/0'  # Redis backend URL
    # Perform the necessary tasks to evaluate the model and generate the score
    score = evaluate_model(job_data)

    # Store the score in a JSON file
    score_file_path = f"score_{job_id}.json"
    with open(score_file_path, "w") as score_file:
        json.dump(score, score_file)

    # Store this result into database too

# API endpoint for creating a job
@app.post("/jobs")
def create_job(job_data: dict):
    # Generate a unique job ID
    job_id = str(uuid.uuid4())

    # Create a new job with status "Pending"
    job = Job(id=job_id, name=job_data["name"], status="Pending")

    # Store the job status in MongoDB
    jobs_collection.insert_one(job.dict())

    # Start the Celery task asynchronously
    process_job.delay(job_id, job_data)

    # Return the job information
    return job

# API endpoint for stopping a job
@app.put("/jobs/{job_id}/stop")
def stop_job(job_id: str):

    # Find the job in the database
    job = jobs_collection.find_one({"id": job_id})

    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    if job["status"] != "Pending":
        raise HTTPException(status_code=400, detail="Only pending jobs can be stopped")

    # TODO: Stop the worker, remove from queue 

    # Update the job status to "Stopped"
    jobs_collection.update_one({"id": job_id}, {"$set": {"status": "Stopped"}})

    # Return a success message
    return {"message": "Job stopped successfully"}


# API endpoint for describing a job
@app.get("/jobs/{job_id}")
def describe_job(job_id: str):
    # Find the job in the database
    job = jobs_collection.find_one({"id": job_id})

    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    # Create a job object with the job details
    job = Job(id=job["id"], name=job["name"], status=job["status"])

    # Return the job information
    return job

# API endpoint for listing all jobs
@app.get("/jobs")
def list_jobs():

    # Retrieve all jobs from the database
    job_records = jobs_collection.find()

    # Create a list of Job objects from the job records
    jobs = []
    for job_record in job_records:
        job = Job(id=job_record["id"], name=job_record["name"], status=job_record["status"])
        jobs.append(job)

    # Return the list of jobs
    return jobs


def evaluate_model(job_data: dict):
    # Replace this function with your actual model evaluation code
    # Perform the necessary tasks to evaluate the model and generate the score
    # ...

    # Return the generated score
    time.sleep(random.randint(1,5))
    return {"score": 0.8}

# Run the FastAPI app
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

