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

payloadFileName = "syscallsPerPayload.txt"
openport = {151, 154, 156, 157, 158, 163, 164, 165, 166, 167, 168, 173, 175, 176, 177, 178, 179, 180, 187, 188, 189, 190, 191, 192, 197, 198, 199, 200, 201, 889, 884, 870, 978, 858, 873,882,881,872,852,847,837,836,835,804,238,684,259,832,834,253,252,965,672,217,357,481,370,501,553,656,655,678,679,366,209,235,515,559}
connect = {152, 153,155,159,169, 170,171,172,174, 181,182,183, 184, 185, 193,194,195,196, 202,907,895,890,871,859,857,552,367,206,883,849,838,207,239,685,208,833,771,242,964}
fileOps	={160,161,186,896,891,888,880,879,878,867,801,894,893,887,885,87,864,862,861,848,842,561,584,258,257,812,765,611,211,353,962,407,963,824,973,255,254,554,799,311,543,875,784,548,755,355,562,563,573,566,369}
execute = {150,162,216,905,892,877,683,806,822,823,815,816,817,818,577,576,602,605,289,906,902,900,624,758,608,399,236,604,954,975,974,361,953,247,225,224,205,810,808,809,807,571,555,249,223,229,248,231,246,233,245,556,546,557,58,544,752,545,798,363,542,564,565,517,516,551,961,578,396,590,220,465,466,244,682,621,642,641,643,639,638,653,636,625,632,623,626,633,622,631,630,634,575,959,227,230,234,232,228,226,540,952,261,221,886,876,869,868,863,851,846,845,844,843,841,840,560,204,690,237,550,547,549,955,756,541,250,251,831,829,827,828,825,813,811,740,741,491,606,607,574,210,957,214,212,213,222,586,587,584,593,585,589,597,599,598,218,219,35,354,358,256,958,951,215,805,365,483,477,476,470,472,473,960,368,505,506,619,650,610,856,850,775,770,558,}

# Getting NUmber of payloads of each kind
openportCount = 0
connectCount = 0
fileOpsCount = 0
executeCount = 0
totalCount = 0
with open(os.path.join(__location__, payloadFileName)) as payloadFilePtr:
	line1 = payloadFilePtr.readline()
	while line1:
		totalCount+=1
		basePayload = line1[:3]
		if len(basePayload) == 1:
			line1 = payloadFilePtr.readline()
			continue;
		if int(basePayload) in openport:
			openportCount+=1;
		elif int(basePayload) in connect:
			connectCount+=1;
		elif int(basePayload) in fileOps:
			fileOpsCount+=1;
		elif int(basePayload) in execute:
			executeCount+=1;
                else:
                    print("Not found: " + basePayload)
		line1 = payloadFilePtr.readline();			
payloadFilePtr.close()

totalCountDiv = (float(totalCount))/100
openportCountDiv = (float(openportCount))/100
connectCountDiv = (float(connectCount))/100
fileOpsCountDiv = (float(fileOpsCount))/100
executeCountDiv = (float(executeCount))/100

print("\t\t\t\t-------------------------------------------------------")
print("\t\t\t\t\t\tTotal Shellcode count: " + str(totalCount))
print("\t\t\t\t-------------------------------------------------------")
print("\t\t\t\tOpenPort\tConnect\t\tExecute\t\tSystemOps")
print("\t\t\t\t("+str(openportCount)+")\t\t("+str(connectCount)+")\t\t("+str(executeCount)+")\t\t(" + str(fileOpsCount)+")")
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
            openportCount = 0
            connectCount = 0
            fileOpsCount = 0
            executeCount = 0
            with open(os.path.join(__location__, payloadFileName)) as payloadFilePtr:
                line1 = payloadFilePtr.readline().strip()
                while line1:
                    payload = line1.split(" ")[0][:-1]
                    usedSyscallsInPayload = line1.split(" ")[1].strip().split(",")
                    payloadIndex = 0
                    while payloadIndex < len(usedSyscallsInPayload):
                        if usedSyscallsInPayload[payloadIndex] in blockedSyscallsInApp:
                            basePayload = payload[:3]
                            if int(basePayload) in openport:
                               openportCount+=1;
                            elif int(basePayload) in connect:
				        		    	      connectCount+=1;
                            elif int(basePayload) in fileOps:
                                fileOpsCount+=1;
                            elif int(basePayload) in execute:
                                executeCount+=1;
                            result.write(payload)
                            result.write(",")
                            count += 1
                            break
                        else:
                            payloadIndex+=1
                    line1 = payloadFilePtr.readline();				
            result.write("("+str(count)+")" + "["+str(openportCount) + "," + str(connectCount) + "," + str(executeCount) + "," + str(fileOpsCount) + "]" )
            print("Blocked:("+str(count)+")\t\t\t" + "["+str(openportCount) + ",\t\t" + str(connectCount) + ",\t\t" + str(executeCount) + ",\t\t" + str(fileOpsCount) + "]" )
            print("Percentage:("+str(round(count/totalCountDiv,2))+")\t\t" + "["+str(round(openportCount/openportCountDiv,2)) + ",\t\t" + str(round(connectCount/connectCountDiv,2)) + ",\t\t" + str(round(executeCount/executeCountDiv,2)) + ",\t\t" + str(round(fileOpsCount/fileOpsCountDiv,2)) + "]\n" )
            payloadFilePtr.close()
            line=blockSys.readline()
    blockSys.close()


print("===================================")
print("===== Via Library Debloating ======")
print("===================================")


get_blocked_payloads(args.blockedSyscallsLibDeb,os.path.join(__location__,"resultViaLibDebloating.txt"))

print("====================================")
print("=== Via Temporal Specialization ====")
print("====================================")


get_blocked_payloads(args.blockedSyscallsTempSpl,os.path.join(__location__,"resultViaTemporalSpecialization.txt"))

