# Evaluation of Security Impact of Temporal Specialization

1. Generate set of blocked system calls for every application via Library 
Debloating and add it to a file: removedViaLibSpecialization.txt
in format
	[Application_Name]:syscall1,syscall2,..

2. Generate set of blocked system calls for every application via Temporal 
Specialization and add it to a file: removedViaTemporalSpecialization.txt
in format
	[Application_Name]:syscall1,syscall2,..

3. List of Shellcode exploits with their IDs and used system calls is in 
syscallsPerPayload.txt .

4. To get number of shellcodes broken by Library Debloating vs those broken
by Temporal Specialization, run
	python getBlockedPayloads.py [--blockedSyscallsTempSpl <FileName>] [--blockedSyscallsLibDeb <FileName>]

FileName contains list of payloads blocked by Temporal Specialization.
If no file is specified, by default it runs for all applications.

After running: 
List of shellcodes broken by Library Debloating: resultViaLibDebloating.txt
List of shellcodes broken by Temporal Specialization: resultViaTemporalSpecialization.txt

5. List of ROP exploits with their IDs and used system calls is in 
syscallsPerPayloadROP.txt .

6. To get number of ROP payloads broken by Library Debloating vs those broken
by Temporal Specialization, run
	python getBlockedPayloadsROP.py [--blockedSyscallsTempSpl <FileName>] [--blockedSyscallsLibDeb <FileName>]

FileName contains list of system calls blocked by Temporal Specialization.
If no file(s) are specified, by default it runs for all applications.

After running:
List of ROP payloads broken by Library Debloating: resultViaLibDebloatingROP.txt
List of ROP payloads broken by Temporal Specialization: resultViaTemporalSpecializationROP.txt
