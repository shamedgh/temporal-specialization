payloadFileName = "syscallsPerPayloadROP.txt"
print("===================================")
print("=== Via Library Specialization ====")
print("===================================")

blockedSysCallFile = "removedViaLibSpecialization.txt"
result = open("resultViaLibSpecializationROP.txt","w")
with open(blockedSysCallFile) as blockSys:
    line=blockSys.readline()
    while line: 
        app = line.split(":")[0].strip()
        print("=== " + app + " ===");
        count = 0
        blockedSyscallsInApp = line.split(":")[1].strip().split(",")
        result.write(app)
        result.write(":")
        with open(payloadFileName) as payloadFilePtr:
    	    line1 = payloadFilePtr.readline()
	    while line1:
		payload = line1.split(" ")[0][:-1]
        	usedSyscallsInPayload = line1.split(" ")[1].strip().split(",")
		payloadIndex = 0
		while payloadIndex < len(usedSyscallsInPayload):
    		    if usedSyscallsInPayload[payloadIndex] in blockedSyscallsInApp:
		    	#Attack is prevented
        		#print("Blocked " + payload + " in " + app + " Missing: " + usedSyscallsInPayload[payloadIndex])
		        #print(payload +  " Missing: " + usedSyscallsInPayload[payloadIndex])
    		        result.write(payload)
		    	result.write(",")
			count += 1
			break
    		    else: 
		    	payloadIndex+=1
    		line1 = payloadFilePtr.readline();				
            result.write("("+str(count)+")")
            result.write("\n")
            print("Blocked(" + str(count)+")")
            payloadFilePtr.close()
            line=blockSys.readline()
blockSys.close()

print("================================")
print("=== Via Temporal Debloating ====")
print("================================")

blockedSysCallFile = "removedViaTemporalDebloating.txt"
result = open("resultViaTemporalDebloatingROP.txt","w")
with open(blockedSysCallFile) as blockSys:
	line=blockSys.readline()
	while line: 
		app = line.split(":")[0].strip()
		print("=== " + app + " ===")
		count = 0
		blockedSyscallsInApp = line.split(":")[1].strip().split(",")
		result.write(app)
		result.write(":")
		with open(payloadFileName) as payloadFilePtr:
			line1 = payloadFilePtr.readline()
			while line1:
				payload = line1.split(" ")[0][:-1]
				usedSyscallsInPayload = line1.split(" ")[1].strip().split(",")
				payloadIndex = 0
				while payloadIndex < len(usedSyscallsInPayload):
					if usedSyscallsInPayload[payloadIndex] in blockedSyscallsInApp:
						#Attack is prevented
						#print("Blocked " + payload + " in " + app + " Missing: " + usedSyscallsInPayload[payloadIndex])
						#print(payload +  " Missing: " + usedSyscallsInPayload[payloadIndex])
						result.write(payload)
						result.write(",")
						count += 1
						break
					else: 
						payloadIndex+=1
				line1 = payloadFilePtr.readline();				
		result.write("("+str(count)+")")
		print("Blocked("+str(count)+")")
		result.write("\n")
		payloadFilePtr.close()
		line=blockSys.readline()
blockSys.close()
	
