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
myInclude = "transaction_sum,location_count"

# read in builder_data.json
with open('builder_data.json', 'w') as json_handle:

	# create country_data entry for country if it does not exists
	if not json_handle.country_data[country]:

		json_handle.country_data[country] = {"info": [1,1], "line":[1,1], "continent":"", "type":"new"}

	 	json.dump(json_full, json_handle, sort_keys = True, indent = 4, ensure_ascii=False)

	# for each raster_data item
	for item in json_handle.raster_data

		rname = item.name
		rfolder = item.folder
		rfile = item.file

		myRaster = '/var/www/html/aiddata/DET/uploads/globals/processed/'+rfolder+'/'+rfile
		myOutput = base+'extract_data/'+country+'_'+sector+'_'+rname+'.csv'
		myName = rname

		src_filename = myRaster
		src_ds=gdal.Open(src_filename) 
		gt=src_ds.GetGeoTransform()
		rb=src_ds.GetRasterBand(1)

		with open(myOutput, 'w') as f:
			header =  myId +","+ myLon +","+ myLat +","

			includes = myInclude.split(",")
			for field in range(0, len(includes)):
				header += includes[field] + ","  
			
			header += myName + "\n" 
			f.write(header)
			
			c = 0

				shp_filename = myData
				ds=ogr.Open(shp_filename)
				lyr=ds.GetLayer()

				for feat in lyr:
					geom = feat.GetGeometryRef()
					field_vals = []

					try:
						feat_id = feat.GetField(myId)
					except:
						feat_id = c

					for field in range(0, len(includes)):
						try:
							field_vals.append( feat.GetField(includes[field]) )
						except:
							field_vals.append( "BAD" )

					
					c += 1

					mx,my=geom.GetX(), geom.GetY()  #coord in map units

					#Convert from map to pixel coordinates.
					#Only works for geotransforms with no rotation.
					px = int((mx - gt[0]) / gt[1]) #x pixel
					py = int((my - gt[3]) / gt[5]) #y pixel

					structval=rb.ReadRaster(px,py,1,1,buf_type=gdal.GDT_Float32)
					intval = struct.unpack('f' , structval) 

					newRow = str(feat_id) + "," + str(mx) + "," + str(my) + "," 

					for field in range(0, len(includes)):
						newRow += str(field_vals[field]) + "," 

					newRow += str(intval[0])+"\n"

					f.write(newRow)

# join extracts

	# OLD PHP JOIN SCRIPT

	# $country = $argv[1];
	# $sector = $argv[2];

	# // open files
	# $base = '/var/www/html/aiddata/data/form/extract_data/'.$country.'_'.$sector;
	# $handles = array();
	# 	$handles[0] = fopen( $base . "_Yield.csv", "r" ); 
	# 	$handles[1] = fopen( $base . "_Income.csv", "r" ); 
	# 	$handles[2] = fopen( $base . "_Urban.csv", "r" ); 
	# $outHandle = fopen('/var/www/html/aiddata/data/form/form_data/'.$country.'_'.$sector.'.csv', "w");

	# // join files
	# while ($fRow = fgetcsv($handles[0])){
	# 	$outRow = $fRow;
	# 	for ($i=1; $i<count($handles); $i++){
	# 		$outRow[] = fgetcsv($handles[$i])[count($fRow)-1];
	# 	}
	# 	fwrite($outHandle, implode($outRow, ",")."\n");
	# }

	# // close files
	# for ($i=0; $i<3; $i++) {		
	# 	fclose( $handles[$i] );
	# }
	# fclose($outHandle);

	# echo "joinExtract.php : done";

