# Temporal Specialization

This repository has been created to help reproduce the results presented in our 
paper *Temporal System Call Specialization for Attack Surface Reduction* presented 
at the 29th Usenix Security Symposium.
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
instructions on how to perform this manually [here](SECCOMP.md)

For the convenience of the artifact evaluators, we provide two ways of
exercising these artifacts. These are (in the order of increasing complexity):

* A prebuilt docker container that can be downloaded and executed.
* Instructions that can be used to replicate our setup on a different
  machine, and run our analysis tool chain.

Because our analysis is a Whole Program Analysis, we need a bitcode that
includes dependent libraries linked together. We have provided this linked
bitcode for the applications that we have reported in our paper (in the
bitcodes/ directory). We have also provided instructions on how to compile
these bitcodes from scratch [here](COMPILE.md)

## Repository Description

The source code along with all the helper scripts are part of this repo. The
important directories and files are ---
* **SVF/**: Contains the modified SVF implementation that we use
* **application-sourcecodes/**: Contains the source code of the applications
* **bitcodes/**: Contains the pre-generated full bitcodes of the applications
* **callgraphs/**: The intermediate and final callgraphs are generated here
* **docker-build/**: Contains the Dockerfile and scripts required to build the
  docker container.
* **python-utils/**: Contains scripts that orchestrate our analysis toolchain
* **security-evaluation/**: Contains scripts that perform the security
  evaluation
* **llvm-7.0.0.src.wclang.tar.xz**: The LLVM+Clang source code
* **stats**: The default path used in the scripts for storing the statistics outputs

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

**Note: Keep in mind that the analysis time varies depending on the complexity
of the application and how large its code base is. We have given estimates on
how long each takes. If it takes long do not worry, it is still running**

```
docker exec -it artifact-eval ./run.sh memcached.libevent
# **Estimated Time Required: 10 minutes**
```

```
docker exec -it artifact-eval ./run.sh httpd.apr
# **Estimated Time Required: 10 minutes**
```

```
docker exec -it artifact-eval ./run.sh nginx
# **Estimated Time Required: 90 minutes**
```

```
docker exec -it artifact-eval ./run.sh lighttpd 
# **Estimated Time Required: 10 minutes**
```

```
docker exec -it artifact-eval ./run.sh redis-server
# **Estimated Time Required: 15 minutes**
```

```
docker exec -it artifact-eval ./run.sh bind.libuv
# **Estimated Time Required: ~10 hours**
```

The results for the analysis will be stored in the path provided in
\<full\_path\_of\_results\_dir\>, in the form
\<app\_name\>.shellcode.payload.txt and \<app\_name\>.rop.payload.txt. These
correspond to the results shown in Table 5 in our paper. (Note: Since the
submission of our paper, we have added more payloads, so the numbers have
changed slightly. But the results are generally similar, and the trends observed and 
reported continue -- temporal specialization outperforms library debloating.)

The file \<app\_name\>.sensitive.stats shows the statistics of the sensitive
system calls that are filtered. This corresponds to Table 3 in our paper. 
Keep in mind that each line in the sensitive.stats file has the following
format:
```
syscall-name;application;debloat-type;1|0
```
To match each line with the table you should only consider the two
debloat-types piecewise-master for library debloating and temporal-worker for
temporal. 1 means the system call is required and 0 means that it is not
required. 
**So 0 is what we would like to see. 0 means that we can filter that sensitive 
system call.**

The file <app\_name>.syscall.count corresponds to Table 2 in our paper. 

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

## Cite our work
```
@inproceedings{temporal2020ghavamnia,
  title={Temporal System Call Specialization for Attack Surface Reduction},
  author={Ghavamnia, Seyedhamed and Palit, Tapti and Mishra, Shachee and Polychronakis, Michalis},
  booktitle={Proceedings of the 29th Usenix Security Symposium},
  year={2020}
}
```
