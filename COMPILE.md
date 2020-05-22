# Compilation of source-code to IR Bitcode

As we mentioned in the [local installation guide](INSTALL.md) you can build
the bitcodes required for running the Temporal Specialization analysis
manually yourself. We have provided a general instruction which corresponds
for all applications and then provided details for applications which might
have specific requirements.

**Warning: Compiling applications from the source code is generally a
troublesome task and may require a lot of debugging, in case the required packages
are not available. We suggest you use the precompiled bitcodes in case you
have not done this before**

## General Guideline
We must use the previously compiled LLVM which you built in [the installation
guide](INSTALL.md). Make sure to change the PATH environment variable to
correspond to where your compiled clang and llvm exist.

*Warning: In case you have another pre-installed llvm and clang instance on
your system, make sure you are using the version provided in our repository
which you compiled manually. If the versions used to compile the application
and SVF do not match it could cause serious problems and the next steps might 
not work and the results might not be valid.*

Generally all the applications we use follow the *configure* and *make*
process for being compiled. We will use the configure command to set our flags
and compiler and then run make.

```
./configure AR=llvm-ar CC=clang CXX=clang++ LD=/usr/bin/ld CFLAGS="-flto -O0" CXXFLAGS="-flto -O0" LDFLAGS="-flto -Wl,-plugin-opt=save-temps"
make
```
The command above should be used for all applications to enable LTO
optimization and generate a single IR bitcode. Multiple **.bc** files will be
generated and you should use the <application>.0.5.precodegen.bc for the next
steps.
Some applications such as Apache Httpd require more options which will be 
discussed below.

## Nginx
We compile all the applications with the default options available in a
vanilla installation. For that reason we need to enable some modules for
Nginx.

```
CC=clang CXX=clang++ LD=/usr/bin/ld CFLAGS="-flto -O0" ./configure --with-http_ssl_module --with-ld-opt="-flto -Wl,-plugin-opt=save-temps"
make
```

## Apache Httpd
Apache Httpd has two special libraries, lib-apr and lib-apr-util, which must 
be either statically compiled with it or linked into the final IR for our 
analysis. It also needs their header files for compilation. There are many
methods to compile Apache but a simple method is to first install the
development package of each library and then compile each element separately
and finally link them together using llvm-link. We will follow this approach
in the steps below.

```
sudo apt install libapr1-dev
sudo apt install libaprutil1-dev
```

### APR Library
The lib-apr source code can be found in the
application-sourcecodes/apr-1.7.0.tar.gz path in the repository. You must
unzip it using the following command:
```
tar -xvf apr-1.7.0.tar.gz
```
Then use the general configure command and then make it.

### APR-util Library
The lib-apr-util source code can be found in the
application-sourcecodes/apr-util-1.6.1.tar.gz path in the repository. You must
unzip it using the following command:
```
tar -xvf apr-util-1.6.1.tar.gz
```
apr-util requires the path to the source code of lib-apr for its compilation.
So we must use the following command to configure it:
```
./configure --with-apr=[path-to-apr-source-code]/apr-1.7.0 CC=clang LD=/usr/bin/ld CFLAGS="-flto -O0" LDFLAGS="-flto -Wl,-plugin-opt=save-temps"
make
```

### Apache Httpd
Apache Httpd can be compiled using the general command provided above. We must
keep in mind that after it is compiled we must combine the bitcode from httpd
and both lib-apr and lib-apr-util libraries into a single bitcode and run the
analysis on that.
The following command can be used to do this.
```
llvm-link [httpd-bitcode] [lib-apr-bitcode] [lib-apr-util-bitcode] -o httpd.bc
```

## Memcached
While memcached can be compiled using the default configure command, it needs
to be compiled with the libevent library. So th libevent library must be
compiled using the command above and linked with memcached using the llvm-link
command, similar to how it was applied for Apache Httpd

## Bind9
Bind9 also requires an extra library named libuv. The source code is provided
in the application-sourcecodes directory. You can unzip and compile it and
combine the bitcode with the bind9's bitcode. Keep in mind that compiling
bind9 generates multiple bitcodes. You should use the
namedtmp0.0.5.precodegen.bc.
