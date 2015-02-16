
# *** form_data.json
# ***  ^^^^^
# *** buildJSON / calc.py
# ***  ^^^^^
# *** sector csv files
# ***  ^^^^^
# *** extract data from AOI rasters
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
in_country = sys.argv[2] # country - country the aid in "in_file" is associated with
in_sector = sys.argv[3] # sector - type of aid the locations in "in_file" represent
in_field =  sys.argv[4] # aid field name - column name aid is located in
in_count = sys.argv[5] # count field name - column name that project count is located in

# projects that have more than this many (as a percentage) projects matching the rasters NODATA value will be given a "no_data" flag in builder_data.json
no_data_limit = 0.25

# output file
in_out = "/var/www/html/aiddata/data/form/form_data.json"

# read in builder_data.json
builder_data_handle = open('/var/www/html/aiddata/data/form/builder_data.json', 'r')

# load raster data from json
builder_data = json.load(builder_data_handle)

try:
	nd_check = builder_data['no_data'][in_country]
except:
	builder_data['no_data'][in_country] = {}

try:
	nd_check = builder_data['no_data'][in_country][in_sector]
except:
	builder_data['no_data'][in_country][in_sector] = {}


# general use blank data
# clear Global->type before it is recalculated using new input data
blank_json_data = {
	"type": in_sector,
	"projects": 0,
	"total": 0
}

# country/sector data
json_data = blank_json_data.copy()

# areas of interest names
categories = []

# update_builder_data = False

for i in range(0, len(builder_data['raster_data'])):

	# column names from input csv containing the raster point extract data
	folder = builder_data['raster_data'][i]['folder']
	# short (hyphenated) name for general use
	name = builder_data['raster_data'][i]['name']

	nodata = builder_data['raster_data'][i]['nodata']

	# log names for later use
	categories.append(name)

	# update fields of blank for later use
	blank_json_data["tot_"+name] = 0
	blank_json_data["per_"+name] = 0

	try: 
		checkcsv_handle = open(in_file, 'r')
		checkcsv_data = csv.DictReader(checkcsv_handle, delimiter=",")
		test = checkcsv_data.next()[folder]
		test = True
		checkcsv_handle.close()

	except:
		test = False

	if test == True:

		json_data["tot_"+name] = 0
		json_data["per_"+name] = 0

		sd = {
			"raw": [],
			"sd": 0,
			"quart": 0,
			"mean": 0,
			"count": 0,
			"nodata":0,
			"thresh": 0
		}

		# determine thresh value for non-fixed items
		if builder_data['raster_data'][i]['stats']['type'] == 'variable':

			precsv_handle = open(in_file, 'r')
			precsv_data = csv.DictReader(precsv_handle, delimiter=",")

			for pre_row in precsv_data:
				sd["raw"].append( float(pre_row[folder]) )

			sd["sd"] = numpy.std(sd["raw"])
			sd["mean"] = numpy.mean(sd["raw"])
			sd["quart"] = numpy.percentile(sd["raw"], 25)

			sd["thresh"] = sd["mean"]

			precsv_handle.close()
		else:
			sd["thresh"] = builder_data['raster_data'][i]['stats']['thresh']



		# build object from processed input data
		csv_handle = open(in_file, 'r')
		csv_data = csv.DictReader(csv_handle, delimiter=",")
		for row in csv_data:

			try:
				aid = float(row[in_field]) / int(row[in_count])
			except:
				aid = 0

			sd['count'] += 1
			if i == 0:
				json_data["projects"] += 1
				json_data["total"] += aid
			
			if float(row[folder]) == float(nodata):
				sd['nodata'] += 1


			if builder_data['raster_data'][i]['stats']['op'] == 'lte' and float(row[folder]) <= sd["thresh"]:
				json_data["tot_"+name] += aid
			elif builder_data['raster_data'][i]['stats']['op'] == 'gte' and float(row[folder]) >= sd["thresh"]:
				json_data["tot_"+name] += aid
			elif builder_data['raster_data'][i]['stats']['op'] == 'eq' and float(row[folder]) == sd["thresh"]:
				json_data["tot_"+name] += aid


		csv_handle.close()

		if json_data["total"] > 0:
			json_data["per_"+name] = 100 * json_data["tot_"+name] / json_data["total"]

		# check nodata vs count
		builder_data['no_data'][in_country][in_sector][name] = False
		if float(sd['nodata']) / float(sd['count']) > no_data_limit:
			builder_data['no_data'][in_country][in_sector][name] = True



builder_data_handle.close()

# dump json back into builder_data.json if any thresh values were updated
# if update_builder_data == True:
with open('/var/www/html/aiddata/data/form/builder_data.json', 'w') as temp_handle:
	json.dump(builder_data, temp_handle, sort_keys = True, indent = 4, ensure_ascii=False)


for cat in categories:
	print cat
print "x"

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


	# ----- UPDATE COUNTRY > SECTOR

	# init input country if it does not exist
	if not in_country in json_full:
		json_full[in_country] = {"Total":{},"Agriculture":{},"Education":{},"Health":{},"Industry":{},"Water":{},"Other":{}}

	# replace input country>type with new json_data
	json_full[in_country][in_sector] = json_data


	# ----- UPDATE COUNTRY > TOTAL

	# clear input country>"Total" before it is recalculated using new input data
	json_full[in_country]["Total"] = blank_json_data.copy()
	json_full[in_country]["Total"]["type"] = "Total"

	# update country>"Total"
	for j_sector in json_full[in_country]:
		print j_sector
		if j_sector != "Total":
			for j_data in json_full[in_country][j_sector]:
				if j_data != "type":
					json_full[in_country]["Total"][j_data] += json_full[in_country][j_sector][j_data]

	# calculate input country>"Total" percentages (above update took sum of all fields)	
	for cat in categories:
		if json_full[in_country]["Total"]["total"] > 0:
			json_full[in_country]["Total"]["per_"+cat] = 100 * json_full[in_country]["Total"]["tot_"+cat] / json_full[in_country]["Total"]["total"]

	# init "Global" if it does not exist
	if not "Global" in json_full :
		json_full["Global"] = {"Total":{},"Agriculture":{},"Education":{},"Health":{},"Industry":{},"Water":{},"Other":{}}


	# ----- UPDATE Global > SECTOR
	# ----- UPDATE Global > TOTAL

	# clear "Global">type amnd "Global">"Total" before it is recalculated using new input data
	json_full["Global"][in_sector] = blank_json_data.copy()
	json_full["Global"]["Total"] = blank_json_data.copy()
	json_full["Global"]["Total"]["type"] = "Total"

	# update Global data
	for j_country in json_full:
		if j_country != "Global" and in_sector in json_full[j_country]:
	
			# update "Global">type
			for j_data in json_full[j_country][in_sector]:
				if j_data != "type":
					json_full["Global"][in_sector][j_data] += json_full[j_country][in_sector][j_data]

			# update "Global">"Total"
			if "Total" in json_full[j_country]:
				for j_data in json_full[j_country]["Total"]:
					if j_data != "type":
						json_full["Global"]["Total"][j_data] += json_full[j_country]["Total"][j_data]

	# calculate "Global" percentages (above update took sum of all fields)
	for cat in categories:
		json_full["Global"][in_sector]["per_"+cat] = 100 * json_full["Global"][in_sector]["tot_"+cat] / json_full["Global"][in_sector]["total"]
		json_full["Global"]["Total"]["per_"+cat] = 100 * json_full["Global"]["Total"]["tot_"+cat] / json_full["Global"]["Total"]["total"]


	# ----- Round all new data

	def rounder(x,y):
		for j_data in json_full[x][y]:
			if j_data != "type":
				json_full[x][y][j_data] = round(json_full[x][y][j_data], 2)

	rounder(in_country, in_sector)
	rounder(in_country, "Total")
	rounder("Global", in_sector)
	rounder("Global", "Total")


# open json for writing
with open(in_out, 'w') as json_handle:
	# dump json back into file
 	json.dump(json_full, json_handle, sort_keys = True, indent = 4, ensure_ascii=False)

print "calc.py : finished ( " +in_country+" "+in_sector+ ")"
