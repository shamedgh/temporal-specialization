import sys

svfcfg = sys.argv[1]
cfgfile = open(svfcfg, 'r')

'''
Node0x55ebaa266db0 [shape=record,shape=circle,label="{log_loglevel}"];
	Node0x55ebaa266db0 -> Node0x55ebaa266e30[color=black];
	Node0x55ebaa25c430 [shape=record,shape=Mrecord,label="{apr_filepath_encoding}"];
	Node0x55ebaa27c7d0 [shape=record,shape=circle,label="{parse_errorlog_misc_string}"];
	Node0x55ebaa27c7d0 -> Node0x55ebaa243530[color=black];
	Node0x55ebaa247dd0 [shape=record,shape=Mrecord,label="{apr_brigade_destroy}"];
	Node0x55ebaa2a4b70 [shape=record,shape=circle,label="{disable_listensocks}"];
	Node0x55ebaa2a4b70 -> Node0x55ebaa252990[color=black];
	Node0x55ebaa2a4b70 -> Node0x55ebaa2621b0[color=black];
	Node0x55ebaa25a190 [shape=record,shape=Mrecord,label="{apr_thread_pool_tasks_count}"];
	Node0x55ebaa26a530 [shape=record,shape=circle,label="{ap_shutdown_conn}"];
	Node0x55ebaa26a530 -> Node0x55ebaa247d50[color=black];

'''
addrToFuncName = dict()
cfgline = cfgfile.readline()
while ( cfgline ):
    #print (cfgline)
    if ( cfgline.strip().startswith("Node") and cfgline.find("label") != -1 ):
        splittedLine = cfgline.split()
        addr = splittedLine[0]
        params = cfgline.replace(addr, "").split(",")
        for param in params:
            #print ("param: " + param)
            if ( param.startswith("label") ):
                #print ("param: " + param)
                name = param
                name = name[name.index("{")+1:]
                name = name[:name.index("}")]
                if ( "|" in name ):
                    name = name[:name.index("|")]
                addrToFuncName[addr] = name
        #print ("addr: " + addr + " name: " + name)
    cfgline = cfgfile.readline()


cfgfile = open(svfcfg, 'r')
cfgline = cfgfile.readline()
while ( cfgline ):
    if ( cfgline.strip().startswith("Node") and cfgline.find("->") != -1 ):
        caller = cfgline.split("->")[0].strip()
        callee = cfgline.split("->")[1].strip()
        #print ("callee: " + callee)
        if ( "[" in callee ):
            callee = callee[:callee.index("[")]
        if ( ";" in callee ):
            callee = callee.replace(";", "")
        #Added for srander option which adds sX at the end of function name
        if ( ":" in caller ):
            caller = caller[:caller.index(":")]
        if ( addrToFuncName.get(caller, None) and addrToFuncName.get(callee, None) ):
            print (addrToFuncName[caller] + "->" + addrToFuncName[callee])
        else:
            if ( callee != "Node0x5644c96bb370"):
                print ("Problem with caller: %s or callee: %s, hasn't been defined", caller, callee)
    cfgline = cfgfile.readline()
