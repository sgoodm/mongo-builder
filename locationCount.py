#
# adds "location_count" field with number of locations associated with each project to flat csv
#
# python /home/detuser/Desktop/aiddata_releases/dataSplit.py /home/detuser/Desktop/aiddata_releases/active/Senegal/locations_original.csv /home/detuser/Desktop/aiddata_releases/active/Senegal/locations.csv
#

import struct
import sys
import csv
# import json
# import numpy		

myData = sys.argv[1]
myOutput = sys.argv[2]
myField = "project_id" # sys.argv[4]

if myData[-4:] == ".csv":
	readDelim = ','
else:
	readDelim = '\t'	

if myOutput[-4:] == ".csv":
	writeDelim = ','
else:
	writeDelim = '\t'

# build project_ID count
with open (myData, 'rb') as readCSV:
	csvRead = csv.DictReader(readCSV, delimiter=readDelim)

	project_list = {}
	for row in csvRead:
		project_id = row[myField]

		if project_id in project_list:
			project_list[project_id] += 1
		else:
			project_list[project_id] = 1


# calc split, add new fields and write new csv
with open (myData, 'rb') as updateCSV:
	csvData = csv.DictReader(updateCSV, delimiter=readDelim)

	# add new fields
	csvData.fieldnames.append("location_count")
	# csvData.fieldnames.extend(("count", "new"))

	with open(myOutput, 'wb') as writeCSV:
		csvWrite = csv.DictWriter(writeCSV, delimiter=writeDelim, fieldnames=csvData.fieldnames)

		# write new header
		csvWrite.writeheader()
	
		for row in csvData:
			project_id = row[myField]

			# get new field values for row
			row["location_count"] = project_list[project_id]
			# row["new"] = float(row["total_d_to_2012"]) / project_list[project_id]
			
			# write new row
			csvWrite.writerow(row)


	

