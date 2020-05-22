FROM ubuntu

ENV NUM_CORES 8
ENV ROOT /debloating-vol
ENV GIT_REPO temporal-specialization-artifacts
ENV GIT_REPO_URL https://github.com/shamedgh/temporal-specialization-artifacts.git

# Override these when launching the container
ENV BC my_bitcode
ENV ENTRY my_func


RUN mkdir $ROOT 

RUN apt-get update

RUN DEBIAN_FRONTEND="noninteractive" apt-get install -y libedit-dev libncurses5-dev python-dev cmake build-essential libncurses5-dev python-dev cmake git

RUN apt install -y vim python3

# Clone the repo
WORKDIR $ROOT 
RUN git clone $GIT_REPO_URL
WORKDIR $ROOT/$GIT_REPO

# Build LLVM
RUN tar -Jxvf llvm-7.0.0.src.wclang.tar.xz
RUN mkdir $ROOT/install
RUN mkdir $ROOT/$GIT_REPO/llvm-7.0.0.src/build
WORKDIR $ROOT/$GIT_REPO/llvm-7.0.0.src/build
RUN cmake -G "Unix Makefiles" -DLLVM_TARGETS_TO_BUILD="X86" -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=$ROOT/install ../
RUN make -j $NUM_CORES && make install/strip

# Build SVF
ENV LLVM_DIR=$ROOT/install/bin
ENV PATH=$LLVM_DIR/:$PATH

WORKDIR $ROOT/$GIT_REPO/SVF
RUN ./build.sh
WORKDIR $ROOT/$GIT_REPO/SVF/Release-build
RUN cp $ROOT/$GIT_REPO/SVF/Release-build/bin/* /usr/bin/

# Copy the parameterized run.sh into the container
WORKDIR $ROOT/$GIT_REPO
COPY run.sh $ROOT/$GIT_REPO
# And the spin.sh -- this will ensure the container doesn't exit
COPY spin.sh $ROOT/$GIT_REPO
RUN chmod u+x run.sh
RUN chmod u+x spin.sh
RUN git pull

#CMD ./run.sh $BC $ENTRY
CMD ./spin.sh
