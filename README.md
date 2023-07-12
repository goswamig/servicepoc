# Just run docker-compose and send the request 
docker-compose up --build

# Test
curl -X POST -H "Content-Type: application/json" -d '{"name": "Job 1"}' http://localhost:8000/jobs
curl -X PUT http://localhost:8000/jobs/{job_id}/stop
curl http://localhost:8000/jobs/{job_id}
curl http://localhost:8000/jobs

