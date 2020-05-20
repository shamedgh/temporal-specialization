import os, sys, subprocess, signal
import re

allLib = sys.argv[1]

inputFile = open(allLib, 'r')
inputLine = inputFile.readline()
countPerLib = dict()

while ( inputLine ):
    libName = inputLine[inputLine.rindex("/"):]
    libName = re.sub("-.*so", ".so", libName)
    libName = libName[:libName.index(".so")]
    libName = libName + ".so"
    count = countPerLib.get(libName, 0)
    count += 1
    countPerLib[libName] = count
    inputLine = inputFile.readline()
inputFile.close()

print(sorted(countPerLib.items(), key = lambda kv:(kv[1], kv[0])))
