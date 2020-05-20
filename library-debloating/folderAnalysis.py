import sys
import os
import re

sys.path.insert(0, '../')

import util

class FolderAnalysis:
    def __init__(self, folderPath, otherCfgPath, muslGraph, glibcGraph, logger):
        self.folderPath = folderPath
        self.otherCfgPath = otherCfgPath
        self.muslGraph = muslGraph
        self.glibcGraph = glibcGraph
        self.logger = logger

    def extractLibrarySpecializationPotential(self):
        syscallList = list()

        i = 0
        while i < 400:
            #syscallList.append("syscall(" + str(i) + ")")
            syscallList.append("syscall(" + str(i) + ")")
            syscallList.append("syscall ( " + str(i) + " )")
            syscallList.append("syscall( " + str(i) + " )")
            i += 1

        exceptList = ["access","arch_prctl","brk","close","execve","exit_group","fcntl","fstat","geteuid","lseek","mmap","mprotect","munmap","openat","prlimit64","read","rt_sigaction","rt_sigprocmask","set_robust_list","set_tid_address","stat","statfs","write","setns","capget","capset","chdir","fchown","futex","getdents64","getpid","getppid","lstat","openat","prctl","setgid","setgroups","setuid","stat","io_setup","getdents","clone","readlinkat","newfstatat","getrandom","sigaltstack","getresgid","getresuid","setresgid","setresuid","alarm","getsid","getpgrp", "epoll_pwait", "vfork"]


        myGraph = self.glibcGraph
        if ( util.usesMusl(self.folderPath) ):
            self.logger.warning("Setting libc to MUSL")
            myGraph = self.muslGraph

        libsWithCfg = set()
        libsInLibc = set()
        elfFunctionStarts = set()
        libFunctionStarts = set()
        libFunctionStartsPerLib = dict()

        for fileName in os.listdir(self.otherCfgPath):
            libsWithCfg.add(fileName)

        libsInLibc.add("libc.callgraph.out")
        libsInLibc.add("libcrypt.callgraph.out")
        libsInLibc.add("libdl.callgraph.out")
        libsInLibc.add("libnsl.callgraph.out")
        libsInLibc.add("libnss_compat.callgraph.out")
        libsInLibc.add("libnss_files.callgraph.out")
        libsInLibc.add("libnss_nis.callgraph.out")
        libsInLibc.add("libpthread.callgraph.out")
        libsInLibc.add("libm.callgraph.out")
        libsInLibc.add("libresolv.callgraph.out")
        libsInLibc.add("librt.callgraph.out")

        #iterate over ELF files
        #IF library which has CFG add to graph
        #ELIF binary or library without CFG add to starting nodes
        cfgAvailable = False
        for fileName in os.listdir(self.folderPath):
            self.logger.debug("fileName: %s", fileName)
            if ( fileName.startswith("lib") and fileName != "libs.out"):
                cfgAvailable = True
                tmpFileName = re.sub("-.*so",".so",fileName)
                tmpFileName = tmpFileName[:tmpFileName.index(".so")]
                tmpFileName = tmpFileName + ".callgraph.out"
                self.logger.debug("tmpFileName: %s", tmpFileName)
                if ( tmpFileName in libsWithCfg ):
                    self.logger.debug("adding tmpFileName to CFG: %s", tmpFileName)
                    myGraph.createGraphFromInput(self.otherCfgPath + "/" + tmpFileName, "->")
                elif ( tmpFileName in libsInLibc ):
                    cfgAvailable = True
                else:
                    cfgAvailable = False
            self.logger.debug("cfgAvailable: %s", cfgAvailable)
            if ( not fileName.startswith("lib") ): 
                self.logger.debug("Adding function starts for %s to elfFunctionStarts", fileName)
                functionList = util.extractImportedFunctionsFromLibc(self.folderPath + "/" + fileName, self.logger)
                #if ( not functionList ):
                #    self.logger.warning("Function extraction for file: %s failed!", fileName)
                elfFunctionStarts.update(set(functionList))
            if ( fileName.startswith("lib") and not cfgAvailable ):
                self.logger.debug("Adding function starts for %s to libFunctionStarts", fileName)
                functionList = util.extractImportedFunctionsFromLibc(self.folderPath + "/" + fileName, self.logger)
                #if ( not functionList ):
                #    self.logger.warning("Function extraction for file: %s failed!", fileName)
                libFunctionStarts.update(set(functionList))
                #self.logger.debug("libFunctionStarts: %s", str(libFunctionStarts))
                tmpSet = libFunctionStartsPerLib.get(fileName, set())
                tmpSet.update(set(functionList))
                libFunctionStartsPerLib[fileName] = tmpSet

        tmpSet = set()
        elfSyscalls = set()
        libSyscalls = set()
        libSyscallsPerLib = dict()

        for function in elfFunctionStarts:
            leaves = myGraph.getLeavesFromStartNode(function, syscallList, list())
            tmpSet = tmpSet.union(leaves)

        for syscallStr in tmpSet:
            syscallStr = syscallStr.replace("syscall( ", "syscall(")
            syscallStr = syscallStr.replace("syscall ( ", "syscall(")
            syscallStr = syscallStr.replace(" )", ")")
            syscallNum = int(syscallStr[8:-1])
            elfSyscalls.add(syscallNum)

        tmpSet = set()
        for function in libFunctionStarts:
            leaves = myGraph.getLeavesFromStartNode(function, syscallList, list())
            tmpSet = tmpSet.union(leaves)

        for syscallStr in tmpSet:
            syscallStr = syscallStr.replace("syscall( ", "syscall(")
            syscallStr = syscallStr.replace("syscall ( ", "syscall(")
            syscallStr = syscallStr.replace(" )", ")")
            syscallNum = int(syscallStr[8:-1])
            libSyscalls.add(syscallNum)

        for libName, libFunctionStarts in libFunctionStartsPerLib.items():
            tmpSet = set()
            for function in libFunctionStarts:
                leaves = myGraph.getLeavesFromStartNode(function, syscallList, list())
                tmpSet = tmpSet.union(leaves)

            tmpLibSyscalls = libSyscallsPerLib.get(libName, set())
            for syscallStr in tmpSet:
                syscallStr = syscallStr.replace("syscall( ", "syscall(")
                syscallStr = syscallStr.replace("syscall ( ", "syscall(")
                syscallStr = syscallStr.replace(" )", ")")
                syscallNum = int(syscallStr[8:-1])
                tmpLibSyscalls.add(syscallNum)
            libSyscallsPerLib[libName] = tmpLibSyscalls          

        return elfSyscalls, libSyscalls, libSyscallsPerLib
