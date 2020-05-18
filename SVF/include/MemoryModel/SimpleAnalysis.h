//===- PointerAnalysis.h -- Base class of pointer analyses--------------------//
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
 * PointerAnalysis.h
 *
 *  Created on: Nov 12, 2013
 *      Author: Yulei Sui
 */

#ifndef POINTERANALYSIS_H_
#define POINTERANALYSIS_H_

#include "MemoryModel/PAG.h"
#include "Util/PathCondAllocator.h"

#include <llvm/Analysis/AliasAnalysis.h>
#include <llvm/Analysis/CallGraph.h>	// call graph


class SVFModule;

/*
 * Pointer Analysis Base Class
 */
class SimpleAnalysis {

public:
    /// Pointer analysis type list
    enum PTATY {
        // Whole program analysis
        Simple_PA,		///< Simple PA
        Conditional_PA		///< Conditional PA
    };

private:
    /// Release the memory
    void destroy();
    PathCondAllocator *pathCondAllocator;
protected:

    /// PAG
    static PAG* pag;
    /// Module
    SVFModule svfMod;
    /// Pointer analysis Type
    PTATY ptaTy;

public:
    /// Constructor
    SimpleAnalysis(PTATY ty = Simple_PA);

    /// Type of pointer analysis
    inline PTATY getAnalysisTy() const {
        return ptaTy;
    }

    /// Get/set PAG
    ///@{
    inline PAG* getPAG() const {
        return pag;
    }
    static inline void setPAG(PAG* g) {
        pag = g;
    }
    //@}

    /// Module
    inline SVFModule getModule() const {
        return svfMod;
    }

    /// Destructor
    virtual ~SimpleAnalysis();

    /// Initialization of a pointer analysis, including building symbol table and PAG etc.
    virtual void initialize(SVFModule svfModule);

    /// Create conditional graph
    virtual void createCCFG(SVFModule svfModule);

    /// Collect configuration struct annotations
    virtual void collectConfigStructAnnotations(SVFModule& svfModule);
protected:
    /// Whether to dump the graph for debugging purpose
    bool dumpGraph();

    /// Reset all object node as field-sensitive.
    void resetObjFieldSensitive();

public:
    /// Dump the statistics
    void dumpStat();

    /// Return PTA name
    virtual const std::string PTAName() const {
        return "Pointer Analysis";
    }

};

#endif /* POINTERANALYSIS_H_ */
