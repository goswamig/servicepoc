# remove all container 
docker rm -f $(docker ps -aq)
# remove all volumes
docker volume prune --force
# remove all images  
docker rmi -f $(docker images -aq)

