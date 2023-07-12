# Just run docker-compose and send the request 
docker-compose up --build

# Test
curl -X POST -H "Content-Type: application/json" -d '{"name": "Job 1", "data": {"parameter1": "value1", "parameter2": "value2"}}' http://localhost:8000/jobs


### running service
##docker build -t my-fastapi-service .
##docker run -d -p 8000:8000 my-fastapi-service
##
### running Redis for celery 
##docker pull redis
##docker run -d --name my-redis-container -p 6379:6379 redis

# Test 
curl -X POST -H "Content-Type: application/json" -d '{"name": "Job 1", "data": {"parameter1": "value1", "parameter2": "value2"}}' http://localhost:8000/jobs



