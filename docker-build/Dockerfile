FROM ubuntu

ENV NUM_CORES 8
ENV ROOT /debloating-vol
ENV GIT_REPO temporal-specialization-artifacts

RUN mkdir $ROOT 

RUN apt-get update

RUN DEBIAN_FRONTEND="noninteractive" apt-get install -y libedit-dev libncurses5-dev python-dev cmake build-essential libncurses5-dev python-dev cmake git

RUN apt install -y vim python3

# Clone the repo
WORKDIR $ROOT 
RUN git clone https://github.com/shamedgh/temporal-specialization-artifacts.git
WORKDIR $ROOT/$GIT_REPO

# Build LLVM
RUN tar -Jxvf llvm-7.0.0.src.tar.xz
RUN mkdir $ROOT/install
RUN mkdir $ROOT/$GIT_REPO/llvm-7.0.0.src/build
WORKDIR $ROOT/$GIT_REPO/llvm-7.0.0.src/build
RUN cmake -G "Unix Makefiles" -DLLVM_TARGETS_TO_BUILD="X86" -DCMAKE_INSTALL_PREFIX=$ROOT/install ../
RUN make -j $NUM_CORES && make install

# Build SVF
ENV LLVM_DIR=$ROOT/install/bin
ENV PATH=$LLVM_DIR/:$PATH

WORKDIR $ROOT/$GIT_REPO/SVF
RUN ./build.sh
WORKDIR $ROOT/$GIT_REPO/SVF/Release-build
RUN cp $ROOT/$GIT_REPO/SVF/Release-build/bin/* /usr/bin/

# Get the scripts
# HACK: assumes that the temporal-debloating project is cloned in the same directory as Dockerfile
# TODO: Merge later
RUN mkdir $ROOT/temporal-scripts
COPY temporal-debloating $ROOT/temporal-scripts
WORKDIR $ROOT/temporal-scripts

# Copy the parameterized run.sh into the container
COPY run.sh $ROOT/temporal-scripts
RUN chmod u+x run.sh

# Override these when launching the container
ENV BC my_bitcode
ENV ENTRY my_func

CMD ./run.sh $BC $ENTRY
