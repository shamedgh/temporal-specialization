FROM ubuntu

ENV NUM_CORES 8

RUN mkdir /debloating-vol

RUN apt-get update

RUN DEBIAN_FRONTEND="noninteractive" apt-get install -y libedit-dev libncurses5-dev python-dev cmake build-essential libncurses5-dev python-dev cmake git

WORKDIR /debloating-vol
RUN git clone https://github.com/shamedgh/temporal-specialization-artifacts.git
WORKDIR /debloating-vol/temporal-specialization-artifacts
RUN tar -Jxvf llvm-7.0.0.src.tar.xz
RUN mkdir /debloating-vol/install
RUN mkdir /debloating-vol/temporal-specialization-artifacts/llvm-7.0.0.src/build
WORKDIR /debloating-vol/temporal-specialization-artifacts/llvm-7.0.0.src/build
RUN cmake -G "Unix Makefiles" -DLLVM_TARGETS_TO_BUILD="X86" -DCMAKE_INSTALL_PREFIX=/debloating-vol/install ../
RUN make -j $NUM_CORES && make install

ENV LLVM_DIR=/debloating-vol/install/bin
ENV PATH=$LLVM_DIR/:$PATH

WORKDIR /debloating-vol/temporal-specialization-artifacts/SVF
# Remove git pull later
RUN git pull
RUN ./build.sh
CMD /usr/bin/bash
