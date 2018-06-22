#!/usr/bin/python

import os
from os import listdir
import json
from os.path import isfile, join


dir = os.path.dirname(__file__)
scriptlist = [f for f in listdir(os.path.join(dir,'scripts')) if isfile(join(os.path.join(dir,'scripts'), f))]
missing = []
missingrns = []
tlslite = json.load(open(os.path.join(dir,'tests/tlslite-ng.json')))
tlslitern = json.load(open(os.path.join(dir,'tests/tlslite-ng-random-subset.json')))
for f in scriptlist:
	if f not in str(tlslite):
		missing.append(f)
	if f not in str(tlslitern):
		missingrns.append(f)

if not missing and not missingrns:
	print(" All scripts are int the json files")
elif set(missing) == set(missingrns):
	print("There are " + str(len(missing)) + " scripts that are missing on both tlslite-ng.json and tlslite-ng.json :")
	print("\n".join(missing))
else:
	print("There are " + str(len(missing)) + " scripts that are missing on tlslite-ng.json : ")
	print("\n".join(missing))
	print("There are " + str(len(missingrns)) + " scripts that are missing on tlslite-ng.json : ".format(len(missingrns)))
	print("\n".join(missingrns))
