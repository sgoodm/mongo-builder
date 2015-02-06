# 
# creates a mongoimport ready JSON-like file combining the projects.tsv, locations.tsv and transactions.tsv 
# files for Senegal format research releases
# 
# use:
# python /home/Desktop/aiddata_releases/buildMongo.py /home/user/Desktop/aiddata_releases/active/Senegal
#
# to import into mongo use:
# mongoimport --db Senegal --collection complete --type json --file /home/user/Desktop/aiddata_releases/active/Senegal/complete.json
#

import sys
import csv
import simplejson as json
from decimal import *
# import pymongo

# folder data is located in. example: /home/user/Desktop/aiddata_releases/active/Senegal
in_folder = sys.argv[1]


files = {

	"projects" 		: in_folder + '/projects.tsv',
	"locations" 	: in_folder + '/locations.tsv',
	"transactions" 	: in_folder + '/transactions.tsv',
	"ancillary" 	: in_folder + '/ancillary.tsv',
	"complete" 		: in_folder + '/complete.json',
	"readDelim" 	: '\t'
}

num_list = {
	"total_commitments",
	"total_disbursements",
	"transaction_value",
	"transaction_year",
	"precision_code",
	"latitude",
	"longitude"
}

sub_list = {
	"transactions",
	"locations"
}

# read in main projects file
with open (files["projects"], 'r') as projects:
	projectRead = csv.DictReader(projects, delimiter=files["readDelim"])

	# open JSON file for writing
	with open (files["complete"], 'w') as writeJSON:

		# add new data for each project
		for row in projectRead:


			# read in transactions table
			with open (files["transactions"], 'r') as transactions:
				transactionRead = csv.DictReader(transactions, delimiter=files["readDelim"])

				# create new array for table
				row["transactions"] = list()

				# fill object with table contents
				for t_row in transactionRead:

					if row["project_id"] == t_row["project_id"]:

						temp = {}

						for t_key in t_row.keys():

							temp[t_key] = t_row[t_key]

						row["transactions"].append(temp)


			# read in locations table
			with open (files["locations"], 'r') as locations:
				locationRead = csv.DictReader(locations, delimiter=files["readDelim"])

				# create new array for table
				row["locations"] = list()

				# fill object with table contents
				for loc_row in locationRead:

					if row["project_id"] == loc_row["project_id"]:

						loc_temp = {}

						for loc_key in loc_row.keys():

							loc_temp[loc_key] = loc_row[loc_key]

						row["locations"].append(loc_temp)


			# use Decimal on fields specified in num_list
	 		for key in row.keys():
				if key in num_list:
					row[key] = Decimal(row[key])
				elif key in sub_list:
					sub_temp = list()
					for sub in row[key]:
						sub_temp_x = {}
						for sub_key in sub.keys():
							if sub_key in num_list:
								sub_temp_x[sub_key] = Decimal(sub[sub_key])
							else:
								sub_temp_x[sub_key] = sub[sub_key]
						sub_temp.append(sub_temp_x)

					row[key] = sub_temp

			# write row to json
			rowjson = json.dumps(row, ensure_ascii=True, use_decimal=True)
	 		writeJSON.write( rowjson + "\n" )

