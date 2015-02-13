from osgeo import gdal,ogr
import struct
import sys
import csv
import json

base = '/var/www/html/aiddata/data/form/'

country = sys.argv[1]
sector = sys.argv[2]

myData = base+'sector_data/'+country+'_'+sector+'.geojson'
myId = "project_id"
myLon = "longitude"
myLat = "latitude"

# read in builder_data.json
json_handle = open('/var/www/html/aiddata/data/form/builder_data.json', 'r')

# load existing json
json_full = json.load(json_handle)

# json validation
#

# create country_data entry for country if it does not exists
new_country = False
if not json_full['country_data'][country]:
	new_country = True
	json_full['country_data'][country] = {"info": [1,1], "line":[1,1], "continent":"", "type":"new"}

myInclude = "transaction_sum,location_count"
if json_full['country_data'][country]['type'] == "old":
	myInclude = "total_commitments,location_count"

# build header(s)
header =  myId +","+ myLon +","+ myLat

includes = myInclude.split(",")
for field in range(0, len(includes)):
	header += "," + includes[field] 

full_header = header
for item in json_full['raster_data']:
	full_header += "," + item['folder']

# for each raster_data item run extractions and build csv
count = len(json_full['raster_data'])
join = {}

for i in range(0, count):

	rname =  json_full['raster_data'][i]['name']
	rfolder =  json_full['raster_data'][i]['folder']
	rfile =  json_full['raster_data'][i]['file']

	myRaster = '/var/www/html/aiddata/DET/uploads/globals/processed/'+rfolder+'/'+rfile
	myOutput = base+'extract_data/'+country+'_'+sector+'_'+rname+'.csv'

	# load raster
	src_filename = myRaster
	src_ds=gdal.Open(src_filename) 
	gt=src_ds.GetGeoTransform()
	rb=src_ds.GetRasterBand(1)

	# open output for this raster extract
	with open(myOutput, 'w') as f:

		f.write(header + "," + rfolder + "\n")

		shp_filename = myData
		ds=ogr.Open(shp_filename)
		lyr=ds.GetLayer()

		for feat in lyr:
			geom = feat.GetGeometryRef()
			field_vals = []

			feat_id = feat.GetField(myId)

			for field in range(0, len(includes)):
				try:
					field_vals.append( feat.GetField(includes[field]) )
				except:
					field_vals.append( "BAD" )

			mx,my=geom.GetX(), geom.GetY()  #coord in map units

			#Convert from map to pixel coordinates.
			px = int((mx - gt[0]) / gt[1]) #x pixel
			py = int((my - gt[3]) / gt[5]) #y pixel

			structval=rb.ReadRaster(px,py,1,1,buf_type=gdal.GDT_Float32)
			intval = struct.unpack('f' , structval) 

			newRow = str(feat_id) + "," + str(mx) + "," + str(my) 

			for field in range(0, len(includes)):
				newRow += "," + str(field_vals[field]) 

			newRow += "," + str(intval[0])

			f.write(newRow + "\n")

			# END FEATURE LOOP

		# CLOSE EXTRACT FILE

	# open csv for joining
	join[i] = csv.reader(open(myOutput,"r"))

	# END JSON LOOP


# join extracts
joined = open(base+'form_data/'+country+'_'+sector+'.csv','w+')

for row in join[0]:

	outRow = ','.join(row)
	for i in range(1,count):
		outRow += ',' + join[i].next()[len(row)-1]
	
	joined.write( outRow + "\n" )


# update builder_data.json if country is new
if new_country == True:
	# open json for writing
	with open('/var/www/html/aiddata/data/form/builder_data.json', 'w') as json_handle:
		# dump json back into file
	 	json.dump(json_full, json_handle, sort_keys = True, indent = 4, ensure_ascii=False)
