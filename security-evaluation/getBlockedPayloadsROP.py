import argparse
import sys,os
__location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))

parser = argparse.ArgumentParser()
parser.add_argument("--blockedSyscallsTempSpl", type=str, nargs='?', 
        default=os.path.join(__location__,"removedViaTemporalSpecialization.txt"))
parser.add_argument("--blockedSyscallsLibDeb", type=str, nargs='?', 
        default=os.path.join(__location__,"removedViaLibDebloating.txt"))

args = parser.parse_args()

payloadFileName = "syscallsPerPayloadROP.txt"

# Getting NUmber of payloads of each kind
totalCount = 0
with open(os.path.join(__location__, payloadFileName)) as payloadFilePtr:
	line1 = payloadFilePtr.readline()
	while line1:
		totalCount+=1
		basePayload = line1[:3]
		if len(basePayload) == 1:
			line1 = payloadFilePtr.readline()
			continue;
		line1 = payloadFilePtr.readline();			
payloadFilePtr.close()

totalCountDiv = (float(totalCount))/100

print("\t\t\t\t-------------------------------------------------------")
print("\t\t\t\t\t\tTotal ROP payload count: " + str(totalCount))
print("\t\t\t\t-------------------------------------------------------")

appsToTest=[]
with open(args.blockedSyscallsTempSpl) as blockSys:
    line=blockSys.readline()
    while line: 
	appsToTest.append(line.split(":")[0].strip())
        line=blockSys.readline()
	

def get_blocked_payloads(blockedSysCallFile, resultFile):
    result = open(resultFile,"w")
    with open(blockedSysCallFile) as blockSys:
        line=blockSys.readline()
        while line:
            app = line.split(":")[0].strip()
            if app not in appsToTest:
                line=blockSys.readline()
                continue
            print("=== " + app + " ===");
            count = 0
            blockedSyscallsInApp = line.split(":")[1].strip().split(",")
            result.write(app)
            result.write(":")
            with open(os.path.join(__location__, payloadFileName)) as payloadFilePtr:
                line1 = payloadFilePtr.readline().strip()
                while line1:
                    payload = line1.split(" ")[0][:-1]
                    usedSyscallsInPayload = line1.split(" ")[1].strip().split(",")
                    payloadIndex = 0
                    while payloadIndex < len(usedSyscallsInPayload):
                        if usedSyscallsInPayload[payloadIndex] in blockedSyscallsInApp:
                            result.write(payload)
                            result.write(",")
                            count += 1
                            break
                        else:
                            payloadIndex+=1
                    line1 = payloadFilePtr.readline();				
            result.write("("+str(count)+")\n" )
            print("Blocked:("+str(count)+")" )
            print("Percentage:("+str(round(count/totalCountDiv,2))+")\t\t" + "\n" )
            payloadFilePtr.close()
            line=blockSys.readline()
    blockSys.close()

print("===================================")
print("===== Via Library Debloating ======")
print("===================================")

get_blocked_payloads(args.blockedSyscallsLibDeb,os.path.join(__location__,"resultViaLibSpecializationROP.txt"))

print("====================================")
print("=== Via Temporal Specialization ====")
print("====================================")


get_blocked_payloads(args.blockedSyscallsTempSpl,os.path.join(__location__,"resultViaTemporalDebloatingROP.txt"))

