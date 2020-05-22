# Artifacts Evaluation for Temporal Specialization

This repository has been created for the Artifact Evaluation process of Usenix
Security 2020 for the paper *Temporal System Call Specialization for Attack Surface 
Reduction*. 
We have provided the resources to reproduce the main 
results presented in the paper. 

In particular, our artifacts cover:
* The entire toolchain:
    * LLMV Pass for Type-based pruning
    * LLVM Pass for Address-taken pruning
    * Python scripts for generating list of filtered system calls
    * Python scripts for comparing results with library debloating
* Security evaluation - shellcodes and ROP
    * Python scripts to perform security evaluation for shellcodes and ROP payloads

Our artifacts do NOT cover:
* Kernel security evaluation
* Installing SECCOMP filters in applications (We have presented
instructions on how to perform this manually)

For the convenience of the artifact evaluators, we provide two ways of
exercising these artifacts. These are (in the order of increasing complexity):

* A prebuilt docker container that can be downloaded and executed.
* Instructions that can be used to replicate our setup on a different
  machine, and run our analysis tool chain.

Because our analysis is a Whole Program Analysis, we need a bitcode that
includes dependent libraries linked together. We have provided this linked
bitcode for the applications that we have reported in our paper (in the
bitcodes/ directory). We have also provided instructions on how to compile
these bitcodes from scratch in *TODO*

## Repository Description

The source code along with all the helper scripts are part of this repo. The
important directories and files are ---
* **SVF/**: Contains the modified SVF implementation that we use
* **bitcodes/**: Contains the pre-generated full bitcodes of the applications
* **callgraphs/**: The intermediate and final callgraphs are generated here
* **docker-build/**: Contains the Dockerfile and scripts required to build the
  docker container.
* **python-utils/**: Contains scripts that orchestrate our analysis toolchain
* **security-evaluation/**: Contains scripts that perform the security
  evaluation
* **llvm-7.0.0.src.wclang.tar.xz**: The LLVM+Clang source code

## Running the Docker container

The easiest way to use our artifacts is by using the prebuilt Docker image.
The Docker image contains all prequisites (such as LLVM+Clang) installed, and
has a copy of this repository under */debloating-vol*.

To run the Docker image, the Docker engine must be installed on the machine. 
To install Docker
on Ubuntu based systems, use:

```
sudo apt install docker.io
```

Create a directory on your machine where the results of our analysis toolchain
will be stored and mount this on the docker container. The command to do this
is:

```
docker run -d --name artifact-eval --volume <full_path_of_results_dir>:/results taptipalit/temporal-specialization-artifacts:1.0
```

(Note: All docker commands *might* need sudo, depending on the user
configuration on your system)

This will pull the container image and launch it. Then, for each application,
simply run the following commands, at the command line ---

```
docker exec -it artifact-eval ./run.sh memcached.libevent
```

```
docker exec -it artifact-eval ./run.sh httpd.apr
```

```
docker exec -it artifact-eval ./run.sh nginx
```

```
docker exec -it artifact-eval ./run.sh lighttpd 
```

```
docker exec -it artifact-eval ./run.sh redis-server
```

The results for the analysis will be stored in the path provided in
\<full\_path\_of\_results\_dir\>, in the form
\<app\_name\>.shellcode.payload.txt and \<app\_name\>.shellcode.rop.txt. These
correspond to the results shown in Table 5 in our paper. (Note: Since the
submission of our paper, we have added more payloads, so the numbers have
changed slightly. But the results are generally similar, and the trends observed and 
reported continue -- temporal specialization outperforms library debloating.)

To re-run an analysis, the easiest way is to kill the container and start
afresh. The command to do that is:

```
docker rm -f artifact-eval
```

We provide further details on how to build the container from the Dockerfile,
and other useful commands [here](docker-build/README.md).

## Running the artifacts on your machine

Follow the instructions [here](INSTALL.md) to install the artifacts on your local machine.

## Compiling source code to generate bitcode
See [here](COMPILE.md) for details on how to compile the source code to
bitcode for our analysis toolchain.

## Security evaluation details
See [here](security-evaluation/README.md) for more details about our security
evaluation scripts.
