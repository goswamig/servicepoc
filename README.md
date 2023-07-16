# Just run docker-compose and start sending request :) 
docker-compose up --build

# Test
## Create a job
curl -X POST -H "Content-Type: application/json" -d '{"name": "Job1", "model": "gpt-3.5-turbo-0301"}' http://localhost:8000/jobs

## List all jobs 
curl http://localhost:8000/jobs


## Describe a job
curl http://localhost:8000/jobs/{job_id}


## Stop a job
curl -X PUT http://localhost:8000/jobs/{job_id}/stop


# CAUTION
## Delete all jobs 
curl -X DELETE http://localhost:8000/jobs


# For UI launch
Goto frontend folder and run `npm start` and visit `http://localhost:3000`
if there is any error for package just do `npm install <package name>`
