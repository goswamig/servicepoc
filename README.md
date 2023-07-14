# Just run docker-compose and send the request 
docker-compose up --build

# Test
curl -X POST -H "Content-Type: application/json" -d '{"name": "Job1", "model": "gpt-3.5-turbo-0301"}' http://localhost:8000/jobs
curl -X PUT http://localhost:8000/jobs/{job_id}/stop
curl http://localhost:8000/jobs/{job_id}
curl http://localhost:8000/jobs

# CAUTION
curl -X DELETE http://localhost:8000/jobs

