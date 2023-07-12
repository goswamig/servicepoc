from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from celery import Celery
from pymongo import MongoClient
import uuid
import json

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

# API endpoint for creating a job
@app.post("/jobs")
def create_job(job_data: dict):
    # Generate a unique job ID
    job_id = str(uuid.uuid4())

    # Start the Celery task asynchronously
    process_job.delay(job_id, job_data)

    # Create a new job with status "Pending"
    job = Job(id=job_id, name=job_data["name"], status="Pending")

    # Store the job status in MongoDB
    jobs_collection.insert_one(job.dict())

    # Return the job information
    return job

# API endpoint for stopping a job
@app.put("/jobs/{job_id}/stop")
def stop_job(job_id: str):
    # Query the Celery task to get the job status
    task = celery_app.AsyncResult(job_id)

    if task.state != "PENDING":
        # If the task is no longer in the PENDING state, raise an exception indicating it cannot be stopped
        raise HTTPException(status_code=400, detail="Only pending jobs can be stopped")

    # Revoke the task to stop its execution
    task.revoke()

    # Return a success message
    return {"message": "Job stopped successfully"}

# API endpoint for describing a job
@app.get("/jobs/{job_id}")
def describe_job(job_id: str):
    # Query the Celery task to get the job status
    task = celery_app.AsyncResult(job_id)

    if task.state == "PENDING":
        raise HTTPException(status_code=404, detail="Job not found")

    # Create a job object with the task status
    job = Job(id=job_id, name=task.info["name"], status=task.state)

    # Return the job information
    return job

# API endpoint for listing all jobs
@app.get("/jobs")
def list_jobs():
    # Retrieve all task IDs from the Celery backend
    task_ids = celery_app.control.inspect().active().keys()

    # Query the status of each task and create Job objects
    jobs = []
    for task_id in task_ids:
        task = celery_app.AsyncResult(task_id)
        job = Job(id=task.id, name=task.info["name"], status=task.state)
        jobs.append(job)

    # Return the list of jobs
    return jobs

def evaluate_model(job_data: dict):
    # Replace this function with your actual model evaluation code
    # Perform the necessary tasks to evaluate the model and generate the score
    # ...

    # Return the generated score
    return {"score": 0.8}

# Run the FastAPI app
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

