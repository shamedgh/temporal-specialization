import os, sys, subprocess, signal
import json
import util

class RepoStaticAnalysis():
    """
    This class can be used to extract information regarding a container created from a docker image
    """
    def __init__(self, repopath, logger):
        self.logger = logger
        self.repopath = repopath
        self.fileFuncDefDict = dict()

    '''
    TODO:
    1. function to convert [commitId], fileName, lineNumber to function
    2. 
    '''

    def getRepoPath(self):
        return self.repopath

    def getFunction(self, fileName, lineNumber, commitId=""):
        self.logger.info("Getting function from file: %s, line: %d", fileName, lineNumber)
        funcLineNumber = lineNumber
        functionDefDict = dict()
        checkoutStatus = True
        if ( commitId != "" ):
            checkoutStatus = self.checkoutFile(commitId, fileName)
        if ( checkoutStatus ):
            functionDefDict = self.getFunctionDefsInFile(fileName, commitId)
            lineNumberList = list(functionDefDict.keys())
            if ( len(lineNumberList) > 0 ):
                self.logger.debug("lineNumberList: %s", str(lineNumberList))
                tmpFilter = filter(lambda i: i <= lineNumber, lineNumberList)
                try:
                    funcLineNumber = max(tmpFilter)
                except ValueError:
                    self.logger.warning("Line number: %d in file: %s and commitId: %s not related to any function definition", lineNumber, fileName, commitId)
            else:
                self.logger.warning("No function definitions found in file: %s", fileName)
        return functionDefDict.get(funcLineNumber, "")

    def checkoutFile(self, commitId, fileName):
        cmd = "cd {}; git checkout {} {}"
        cmd = cmd.format(self.repopath, commitId, fileName)
        returncode, out, err = util.runCommand(cmd)
        if ( returncode != 0 ):
            self.logger.error("Error running checkout command: %s", err)
            return False
        return True

    def getFunctionDefsInFile(self, fileName, commitId):
        fileNameCommitTuple = (fileName, commitId)
        self.logger.debug("fileNameCommit tuple: %s", str(fileNameCommitTuple))
        functionDefDict = dict()
        tmpDict = self.fileFuncDefDict.get(fileNameCommitTuple, None)
        if ( tmpDict ):
            self.logger.debug("fileNameCommit tuple has been already extracted: %s", str(fileNameCommitTuple))
            return tmpDict
        firstCmd = "cd {}; cscope -R -L -1 \".*\" 2>/dev/null | grep \"{}\" | sed -e 's/^[ \t]*//' | grep -v \"^struct\""
        firstCmd = firstCmd.format(self.repopath, fileName)
        returncode, firstOut, err = util.runCommand(firstCmd)
        if ( returncode != 0 ):
            self.logger.error("Error running first cscope command: %s error: %s", firstCmd, err)
            return functionDefDict
#        secondCmd = "cd {}; cscope -R -L -1 \".*\" 2>/dev/null | grep \"{}\" | grep \", struct \""
#        secondCmd = secondCmd.format(self.repopath, fileName)
#        returncode, secondOut, err = util.runCommand(secondCmd)
#        if ( returncode != 0 ):
#            self.logger.error("Error running cscope command: %s error: %s", secondCmd, err)
#            return functionDefDict
        '''
mm/gup.c .* 29 unsigned int page_mask;
mm/gup.c .* 32 typedef int (*set_dirty_func_t)(struct page *page);
mm/gup.c .* 34 static void __put_user_pages_dirty(struct page **pages,
mm/gup.c .* 87 void put_user_pages_dirty(struct page **pages, unsigned long npages)
mm/gup.c .* 108 void put_user_pages_dirty_lock(struct page **pages, unsigned long npages)
mm/gup.c .* 123 void put_user_pages(struct page **pages, unsigned long npages)
mm/gup.c .* 138 static struct page *no_page_table(struct vm_area_struct *vma,
mm/gup.c .* 154 static int follow_pfn_pte(struct vm_area_struct *vma, unsigned long address,
        '''
        #TODO check if we're correctly extracting function definitions from the cscope output
        out = firstOut# + "\n" + secondOut
        outLines = out.splitlines()
        for outLine in outLines:
            if ( "(" in outLine ):
                splittedOut = outLine.split("(")
                if ( not splittedOut[0].endswith(" ") ):
                    funcArgs = splittedOut[1]
                    splittedOut = splittedOut[0].split()
                    funcName = splittedOut[-1]
                    if ( funcName.startswith("SYSCALL_DEFINE") ):
                        if ( "," in funcArgs ):
                            funcArgs = funcArgs[:funcArgs.index(",")]
                        funcName = "__x64_sys_" + funcArgs
                    cscopeFileName = splittedOut[0].strip()
                    lineNumber = int(splittedOut[2])
                    if ( cscopeFileName == fileName ):
                        functionDefDict[lineNumber] = funcName

        self.fileFuncDefDict[fileNameCommitTuple] = functionDefDict

        return functionDefDict
