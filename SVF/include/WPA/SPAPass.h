//===- WPAPass.h -- Whole program analysis------------------------------------//
//
//                     SVF: Static Value-Flow Analysis
//
// Copyright (C) <2013-2017>  <Yulei Sui>
//

// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.

// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.

// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <http://www.gnu.org/licenses/>.
//
//===----------------------------------------------------------------------===//


/*
 * @file: WPA.h
 * @author: yesen
 * @date: 10/06/2014
 * @version: 1.0
 *
 * @section LICENSE
 *
 * @section DESCRIPTION
 *
 */


#ifndef WPA_H_
#define WPA_H_

#include "MemoryModel/SimpleAnalysis.h"
#include <llvm/Analysis/TargetLibraryInfo.h>
#include <llvm/Pass.h>

class SVFModule;

/*!
 * Whole program pointer analysis.
 * This class performs various pointer analysis on the given module.
 */
// excised ", public llvm::AliasAnalysis" as that has a very light interface
// and I want to see what breaks.
class SPAPass: public llvm::ModulePass {
    typedef std::vector<SimpleAnalysis*> PTAVector;

public:
    /// Pass ID
    static char ID;

    /// Constructor needs TargetLibraryInfo to be passed to the AliasAnalysis
    SPAPass() : llvm::ModulePass(ID) {

    }

    /// Destructor
    ~SPAPass();

    virtual inline void getAnalysisUsage(llvm::AnalysisUsage &au) const {
        // declare your dependencies here.
        /// do not intend to change the IR in this pass,
        au.setPreservesAll();
    }

    /// Get adjusted analysis for alias analysis
    virtual inline void* getAdjustedAnalysisPointer(llvm::AnalysisID id) {
        return this;
    }

    /// We start from here
    virtual bool runOnModule(llvm::Module& module) {
        return false;
    }

    /// Run pointer analysis on SVFModule
    void runOnModule(SVFModule svfModule);

    /// PTA name
    virtual inline llvm::StringRef getPassName() const {
        return "SPAPass";
    }

private:
    /// Create pointer analysis according to specified kind and analyze the module.
    void runSimpleAnalysis(SVFModule svfModule, u32_t kind);

    PTAVector ptaVector;	///< all pointer analysis to be executed.
    SimpleAnalysis* _pta;	///<  pointer analysis to be executed.
};


#endif /* WPA_H_ */
