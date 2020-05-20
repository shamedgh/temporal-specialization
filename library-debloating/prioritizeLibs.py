import os, sys, subprocess, signal
import re

allLib = sys.argv[1]

inputFile = open(allLib, 'r')
inputLine = inputFile.readline()
countPerLib = dict()

while ( inputLine ):
    inputLine = inputLine.strip()
    libName = inputLine.split()[0]
    newCount = int(inputLine.split(":")[1])
    libName = re.sub("-.*so", ".so", libName)
    libName = libName[:libName.index(".so")]
    libName = libName + ".so"
    count = countPerLib.get(libName, 0)
    if ( newCount > count ):
        countPerLib[libName] = newCount
    inputLine = inputFile.readline()
inputFile.close()

sortedList = sorted(countPerLib.items(), key = lambda kv:(kv[1], kv[0]))
for item in sortedList:
    print (str(item[0]) + ":" + str(item[1]))
