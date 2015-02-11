
# *** form_data.json
# ***  ^^^^^
# *** buildJSON / calc.py
# ***  ^^^^^
# *** sector csv files
# ***  ^^^^^
# *** PET (using indicator rasters)
# ***  ^^^^^
# *** geojson of points
# ***  ^^^^^
# *** ogr2ogr
# ***  ^^^^^
# *** csv + vrt
# ***  ^^^^^
# *** mongo
# ***  ^^^^^
# *** research release

import struct
import sys
import csv
import json
import numpy

#sys.argv[0] is file name sent to python

in_file = sys.argv[1] # file - csv file containing results from Point Extraction Tool

in_type = sys.argv[2] # sector - type of aid the locations in "in_file" represent

in_country = sys.argv[3] # country - country the aid in "in_file" is associated with

in_field =  sys.argv[4] # aid field name - column name aid is located in

in_count = sys.argv[5] # count field name - column name that project count is located in


# in_ag = sys.argv[4] #low agricultural productivity 
# in_ag = 2

# in_ec = sys.argv[5] #low economic activity
# in_ec = 975

# in_ur = 2 #input not needed since urban / rural uses binary

# in_ed = sys.argb[] #current do not have education / literacy data

# output file
in_out = "/var/www/html/aiddata/data/form/form_data.json"

# column names from input csv containing the raster point extract data
ag_name = "agriculture__actual_potential_yield_gap__2000"
ec_name = "socioeconomics__local_economic_activity__1995"
ur_name = "socioeconomics__urban_areas__1995"


sd = {
	"ag":{
		"raw": [],
		"sd": 0,
		"quart": 0,
		"mean": 0,
		"thresh": 0
	},
	"ec":{
		"raw": [],
		"sd": 0,
		"quart": 0,
		"mean": 0,
		"thresh": 0
	},
	"ur":{
		# "raw": [],
		# "sd": 0,
		# "mean": 0,
		"thresh": 2 # PRE SET SINCE THRESH IS BINARY (1:rural, 2:urban)
	}
}

json_data = {
	"type": in_type,
	"projects": 0,
	"total": 0,
	"ag_tot": 0,
	"ag_per": 0,
	"ec_tot": 0,
	"ec_per": 0,
	"ur_tot": 0,
	"ur_per": 0,
	"ed_tot": 0,
	"ed_per": 0
}

#clear Global->type before it is recalculated using new input data
blank_json_data = json_data.copy()

# process input data
with open (in_file, 'rb') as csv_handle:
	pre_csv_data = csv.DictReader(csv_handle, delimiter=",")

	#get standard deviation 
	for pre_row in pre_csv_data:
		sd["ag"]["raw"].append( float(pre_row[ag_name]) )
		sd["ec"]["raw"].append( float(pre_row[ec_name]) )
		# sd["ur"]["raw"].append(float(pre_row["socioeconomics__urban_areas__1995"]))

	sd["ag"]["sd"] = numpy.std(sd["ag"]["raw"])
	sd["ec"]["sd"] = numpy.std(sd["ec"]["raw"])
	# sd["ur"]["sd"] = numpy.std(sd["ur"]["raw"])

	sd["ag"]["mean"] = numpy.mean(sd["ag"]["raw"])
	sd["ec"]["mean"] = numpy.mean(sd["ec"]["raw"])
	# sd["ur"]["mean"] = numpy.mean(sd["ur"]["raw"])

	sd["ag"]["quart"] = numpy.percentile(sd["ag"]["raw"], 25)
	sd["ec"]["quart"] = numpy.percentile(sd["ec"]["raw"], 25)

	# sd["ag"]["thresh"] = sd["ag"]["mean"] - sd["ag"]["sd"]
	# sd["ec"]["thresh"] = sd["ec"]["mean"] - sd["ec"]["sd"]
	sd["ag"]["thresh"] = sd["ag"]["quart"]
	sd["ec"]["thresh"] = sd["ec"]["quart"]

# build object from processed input data
with open (in_file, 'rb') as csv_handle:	
	csv_data = csv.DictReader(csv_handle, delimiter=",")

	for row in csv_data:

		try:
			aid = float(row[in_field]) / int(row[in_count])
		except:
			aid = 0

		ag = float(row[ag_name])
		ec = float(row[ec_name])
		ur = float(row[ur_name])

		json_data["projects"] += 1
		json_data["total"] += aid

		if ag <= sd["ag"]["thresh"]:
			json_data["ag_tot"] += aid # float(row[in_field])

		if ec <= sd["ec"]["thresh"]:
			json_data["ec_tot"] += aid # float(row[in_field])

		if ur == sd["ur"]["thresh"]:
			json_data["ur_tot"] += aid # float(row[in_field])


json_data["total"] = json_data["total"]

json_data["ag_tot"] = json_data["ag_tot"]
json_data["ec_tot"] = json_data["ec_tot"]
json_data["ur_tot"] = json_data["ur_tot"]

json_data["ag_per"] = 100 * json_data["ag_tot"] / json_data["total"]
json_data["ec_per"] = 100 * json_data["ec_tot"] / json_data["total"]
json_data["ur_per"] = 100 * json_data["ur_tot"] / json_data["total"]

# open json for reading
with open(in_out, 'r') as json_handle:

	try:
		# load existing json
		json_full = json.load(json_handle)
	except:
		# init json if file is empty
		json_full = {	
						"Global":{"Total":{},"Agriculture":{},"Education":{},"Health":{},"Industry":{},"Water":{},"Other":{}},
						in_country:{"Total":{},"Agriculture":{},"Education":{},"Health":{},"Industry":{},"Water":{},"Other":{}}
					}



	# init input country if it does not exist
	if not in_country in json_full:
		json_full[in_country] = {"Total":{},"Agriculture":{},"Education":{},"Health":{},"Industry":{},"Water":{},"Other":{}}

	# replace input country>type with new json_data
	json_full[in_country][in_type] = json_data

	# clear input country>"Total" before it is recalculated using new input data
	json_full[in_country]["Total"] = blank_json_data.copy()
	json_full[in_country]["Total"]["type"] = "Total"

	# update country>"Total"
	for j_type in json_full[in_country]:
		if j_type != "Total":
			for j_data in json_full[in_country][j_type]:
				if j_data != "type":
					json_full[in_country]["Total"][j_data] += json_full[in_country][j_type][j_data]			

	# calculate input country>"Total" percentages (above update took sum of all fields)	
	json_full[in_country]["Total"]["ag_per"] = 100 * json_full[in_country]["Total"]["ag_tot"] / json_full[in_country]["Total"]["total"]
	json_full[in_country]["Total"]["ec_per"] = 100 * json_full[in_country]["Total"]["ec_tot"] / json_full[in_country]["Total"]["total"]
	json_full[in_country]["Total"]["ur_per"] = 100 * json_full[in_country]["Total"]["ur_tot"] / json_full[in_country]["Total"]["total"]

	json_full[in_country]["Total"]["total"] = json_full[in_country]["Total"]["total"]



	# init "Global" if it does not exist
	if not "Global" in json_full :
		json_full["Global"] = {"Total":{},"Agriculture":{},"Education":{},"Health":{},"Industry":{},"Water":{},"Other":{}}

	# clear "Global">type amnd "Global">"Total" before it is recalculated using new input data
	json_full["Global"][in_type] = blank_json_data.copy()
	json_full["Global"]["Total"] = blank_json_data.copy()
	json_full["Global"]["Total"]["type"] = "Total"

	# update Global data
	for j_country in json_full:
		if j_country != "Global" and in_type in json_full[j_country]:
			
			# update "Global">type
			for j_data in json_full[j_country][in_type]:
				if j_data != "type":
					json_full["Global"][in_type][j_data] += json_full[j_country][in_type][j_data]
			
			# update "Global">"Total"
			if "Total" in json_full[j_country]:
				for j_data in json_full[j_country]["Total"]:
					if j_data != "type":
						json_full["Global"]["Total"][j_data] += json_full[j_country]["Total"][j_data]

	# calculate "Global" percentages (above update took sum of all fields)	
	json_full["Global"][in_type]["ag_per"] = 100 * json_full["Global"][in_type]["ag_tot"] / json_full["Global"][in_type]["total"]
	json_full["Global"][in_type]["ec_per"] = 100 * json_full["Global"][in_type]["ec_tot"] / json_full["Global"][in_type]["total"]
	json_full["Global"][in_type]["ur_per"] = 100 * json_full["Global"][in_type]["ur_tot"] / json_full["Global"][in_type]["total"]
	
	json_full["Global"]["Total"]["ag_per"] = 100 * json_full["Global"]["Total"]["ag_tot"] / json_full["Global"]["Total"]["total"]
	json_full["Global"]["Total"]["ec_per"] = 100 * json_full["Global"]["Total"]["ec_tot"] / json_full["Global"]["Total"]["total"]
	json_full["Global"]["Total"]["ur_per"] = 100 * json_full["Global"]["Total"]["ur_tot"] / json_full["Global"]["Total"]["total"]


	def rounder(x,y):
		for j_data in json_full[x][y]:
			if j_data != "type":
				json_full[x][y][j_data] = round(json_full[x][y][j_data], 2)

	rounder(in_country, in_type)
	rounder(in_country, "Total")
	rounder("Global", in_type)
	rounder("Global", "Total")



# open json for writing
with open(in_out, 'w') as json_handle:
	# dump json back into file
 	json.dump(json_full, json_handle, sort_keys = True, indent = 4, ensure_ascii=False)