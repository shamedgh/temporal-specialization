1. Build the container

docker build --tag artifacts:1.0 ./

Select the number of cores you want to use to build clang+llvm.

e.g.
docker build --tag artifacts:1.0 ./

2. Run the container

docker run -it --name artifact-eval artifacts:1.0 ./run.sh <bitcode_name> <worker_entrypoint>

e.g. docker run -it --name artifact-eval artifacts:1.0 ./run.sh memcached.libevent worker_libevent

3. Other helpful commands

a. Stop all containers

docker stop $(docker ps -a -q)

b. Delete all containers

docker rm $(docker ps -a -q)

c. Delete all docker images

docker rmi $(docker images -a -q)
