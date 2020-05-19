//===- PointerAnalysis.cpp -- Base class of pointer analyses------------------//
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
 * PointerAnalysis.cpp
 *
 *  Created on: May 14, 2013
 *      Author: rocky
 */

#include "MemoryModel/SimpleAnalysis.h"
#include "MemoryModel/PAGBuilder.h"
#include "Util/AnalysisUtil.h"
#include "Util/PTAStat.h"
#include "Util/CPPUtil.h"
#include "Util/SVFModule.h"
#include <fstream>
#include <sstream>

using namespace llvm;
using namespace analysisUtil;
using namespace cppUtil;

PAG* SimpleAnalysis::pag = NULL;

/*!
 * Constructor
 */
SimpleAnalysis::SimpleAnalysis(PTATY ty) :
    ptaTy(ty) {
}

/*!
 * Destructor
 */
SimpleAnalysis::~SimpleAnalysis() {
    destroy();
    // do not delete the PAG for now
    //delete pag;
}


void SimpleAnalysis::destroy()
{
//    delete ptaCallGraph;
//    ptaCallGraph = NULL;
//
//    delete callGraphSCC;
//    callGraphSCC = NULL;
//
//    delete stat;
//    stat = NULL;
//
//    delete typeSystem;
//    typeSystem = NULL;
}

/*!
 * Initialization of pointer analysis
 */
void SimpleAnalysis::initialize(SVFModule svfModule) {

    /// whether we have already built PAG
    if(pag == NULL) {

        DBOUT(DGENERAL, outs() << pasMsg("Building PAG ...\n"));
        outs() << "Building PAG ...\n";
        // We read PAG from a user-defined txt instead of parsing PAG from LLVM IR
        if (SVFModule::pagReadFromTXT()) {
            PAGBuilderFromFile fileBuilder(SVFModule::pagFileName());
            pag = fileBuilder.build();

        } else {
            outs() << "Building Symbol Table ...\n";
            DBOUT(DGENERAL, outs() << pasMsg("Building Symbol table ...\n"));
            SymbolTableInfo* symTable = SymbolTableInfo::Symbolnfo();
            symTable->buildMemModel(svfModule);

            PAGBuilder builder;
            pag = builder.build(svfModule);

            /// Hamed: print the functions assigned to FPs
            for ( PAG::FunctionAssignmentToFunctionMap::iterator it = pag->getFunAssignmentMap().begin(), eit = pag->getFunAssignmentMap().end(); it != eit; it++ ){
                for ( PAG::FunctionSet::iterator it2 = it->second.begin(), eit2 = it->second.end(); it2 != eit2; it2++ ){
                    //outs() << it->first->getName() << "->" << (*it2)->getName() << "\n";
                    outs() << (*it2)->getName() << "->" << it->first->getName() << "\n";
                }
            }

        }
        outs() << "Finished building PAG ...\n";

        // dump the PAG graph
        //if (dumpGraph())
        //    PAG::getPAG()->dump("pag_initial");

        // print to command line of the PAG graph
        //if (PAGPrint)
        //    pag->print();
    }

}




/*!
 * Initialization of pointer analysis
 */
void SimpleAnalysis::createCCFG(SVFModule svfModule) {
    outs() << "SimpleAnalysis::createCCFG called\n";
    collectConfigStructAnnotations(svfModule);
    pathCondAllocator = new PathCondAllocator();
    pathCondAllocator->allocate(svfModule);

    //pathCondAllocator->fillMaps(&bbToCondition, &falseBBs);
    pathCondAllocator->fillMaps();

    for (SVFModule::iterator fit = svfModule.begin(), efit = svfModule.end();
            fit != efit; ++fit) {
        llvm::Function& fun = **fit;
        std::stack<PathCondAllocator::Condition*> conditionStack;
        for (llvm::Function::iterator bit = fun.begin(), ebit = fun.end();
                bit != ebit; ++bit) {
            llvm::BasicBlock& bb = *bit;
            //outs() << "-----------------------------------------------------\n";
            //outs() << "BB Id: " << pathCondAllocator->getBBId(&bb) << "\n";
            if ( !conditionStack.empty() && pathCondAllocator->isConditionExitNode(&bb, conditionStack.top()) ){
                //outs() << "Popping from conditions stack in BB: " << bb.getName() << " stack size: " << conditionStack.size() << "\n";
                assert(!conditionStack.empty() && "Trying to pop from empty stack!");
                conditionStack.pop();
            }
            if ( pathCondAllocator->isTrueBranchTarget(&bb) ) {
                //outs() << "Adding condition stack for BB: " << bb.getName() << " stack size: " << conditionStack.size() << "\n";
                conditionStack.push(pathCondAllocator->getConditionForBB(&bb));
            }

            for (llvm::BasicBlock::iterator it = bb.begin(), eit = bb.end();
                    it != eit; ++it) {
                llvm::Instruction& inst = *it;
                llvm::Instruction *tmpInst = &*it;

                if (isCallSite(tmpInst) && isInstrinsicDbgInst(tmpInst)==false) {

                    llvm::CallSite cs = analysisUtil::getLLVMCallSite(tmpInst);
                    // Calls to inline asm need to be added as well because the callee isn't
                    // referenced anywhere else.
                    const Value *callee = cs.getCalledValue();
                    if ( isa<llvm::Function>(callee) ){
                        if ( !conditionStack.empty() )
                            outs() << fun.getName() << "->CONDITION-> " << callee->getName() << "\n";
                        else
                            outs() << fun.getName() << "-> " << callee->getName() << "\n";
                    }
                }
            }

        }
    }
}

void SimpleAnalysis::collectConfigStructAnnotations(SVFModule& svfModule){
    std::vector<StringRef> GlobalSensitiveNameList;

    // Get the names of the global variables that are sensitive
    if(GlobalVariable* GA = svfModule.getModuleRef(0).getGlobalVariable("llvm.global.annotations")) {
        for (Value *AOp : GA->operands()) {
            if (ConstantArray *CA = dyn_cast<ConstantArray>(AOp)) {
                for (Value *CAOp : CA->operands()) {
                    if (ConstantStruct *CS = dyn_cast<ConstantStruct>(CAOp)) {
                        if (CS->getNumOperands() < 4) {
                            outs() << "Unexpected number of operands found. Skipping annotation. \n";;
                            break;
                        }

                        Value *CValue = CS->getOperand(0);
                        if (ConstantExpr *Cons = dyn_cast<ConstantExpr>(CValue)) {
                            GlobalSensitiveNameList.push_back(Cons->getOperand(0)->getName());
                        }
                    }
                }
            }
        }
    }
    // Add the global variables which are sensitive to the list
    for (SVFModule::global_iterator tempI = svfModule.global_begin(), E = svfModule.global_end(); tempI != E; ++tempI) {
        GlobalVariable *I = *tempI;
        if (I->getName() != "llvm.global.annotations") {
            GlobalVariable* GV = I;//llvm::cast<GlobalVariable>(&I);
            if (std::find(GlobalSensitiveNameList.begin(), GlobalSensitiveNameList.end(), GV->getName()) != GlobalSensitiveNameList.end()) {
                outs() << "GlobalVariable name: " << GV->getName() << "\n";
                if ( GV->getValueType()->isStructTy() )
                    outs() << "GlobalVariable type: " << GV->getValueType()->getStructName() << "\n";
                else
                    outs() << " Not struct type\n";
                // It might be an object or a pointer, we'll deal with these guys later
//                if (pag->hasObjectNode(GV)) {
//                    NodeID objID = pag->getObjectNode(GV);
//                    PAGNode* objNode = pag->getPAGNode(objID);
//                    SensitiveObjList.push_back(objNode);
//                    // Find all Field-edges and corresponding field nodes
//                    NodeBS nodeBS = pag->getAllFieldsObjNode(objID);
//                    for (NodeBS::iterator fIt = nodeBS.begin(), fEit = nodeBS.end(); fIt != fEit; ++fIt) {
//                        PAGNode* fldNode = pag->getPAGNode(*fIt);
//                        SensitiveObjList.push_back(fldNode);
//                    }
//                    SensitiveObjList.push_back(objNode);
//                }
//                if (pag->hasValueNode(GV)) {
//                    SensitiveObjList.push_back(pag->getPAGNode(pag->getValueNode(GV)));
//                }
            }
        }
    }

}
