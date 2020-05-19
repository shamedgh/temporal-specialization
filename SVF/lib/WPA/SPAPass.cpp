//===- WPAPass.cpp -- Whole program analysis pass------------------------------//
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
//===-----------------------------------------------------------------------===//

/*
 * @file: WPA.cpp
 * @author: yesen
 * @date: 10/06/2014
 * @version: 1.0
 *
 * @section LICENSE
 *
 * @section DESCRIPTION
 *
 */


#include "Util/SVFModule.h"
#include "MemoryModel/SimpleAnalysis.h"
#include "WPA/SPAPass.h"
#include <llvm/Support/CommandLine.h>

using namespace llvm;

char SPAPass::ID = 0;

static RegisterPass<SPAPass> SIMPLEPROGRAMA("spa",
        "Simple Program Analysis Pass");

/// register this into alias analysis group
///static RegisterAnalysisGroup<AliasAnalysis> AA_GROUP(WHOLEPROGRAMPA);

static cl::bits<SimpleAnalysis::PTATY> PASelected(cl::desc("Select simple analysis"),
        cl::values(
			clEnumValN(SimpleAnalysis::Simple_PA, "simple", "Simple analysis for Callgraph and PAG"),
			clEnumValN(SimpleAnalysis::Conditional_PA, "condition-cfg", "Create conditional callgraph")
        ));


/*!
 * Destructor
 */
SPAPass::~SPAPass() {
}

/*!
 * We start from here
 */
void SPAPass::runOnModule(SVFModule svfModule) {
    for (u32_t i = 0; i<= SimpleAnalysis::Conditional_PA; i++) {
        if (PASelected.isSet(i))
            runSimpleAnalysis(svfModule, i);
    }
}


/*!
 * Create pointer analysis according to a specified kind and then analyze the module.
 */
void SPAPass::runSimpleAnalysis(SVFModule svfModule, u32_t kind)
{
    /// Initialize pointer analysis.
    switch (kind) {
    case SimpleAnalysis::Simple_PA:
		_pta = new SimpleAnalysis();
        _pta->initialize(svfModule);
		break;
    case SimpleAnalysis::Conditional_PA:
		_pta = new SimpleAnalysis();
        _pta->createCCFG(svfModule);
        break;
    default:
        assert(false && "This pointer analysis has not been implemented yet.\n");
        return;
    }

    ptaVector.push_back(_pta);
}
