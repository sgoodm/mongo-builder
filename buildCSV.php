<?php

	// --------------------
	// init

	$start_year = intval($argv[2]);
	$end_year = intval($argv[3]);
	$transaction_type = "C";

	$database = $argv[1];
	$collection = "complete";

	$filter = 'ad_sector_names';
	$sector = $argv[4]; // industry name

	$sub_options = array(
			"Agriculture" => array( new MongoRegex("/.*" . "Agriculture" . ".*/i") ),
			"Education"   => array( new MongoRegex("/.*" . "Education" . ".*/i") ),
			"Health"      => array( new MongoRegex("/.*" . "Health" . ".*/i") ),
			"Industry"	  => array( new MongoRegex("/.*" . "Industry" . ".*/i") ),
			"Water"       => array( new MongoRegex("/.*" . "Water" . ".*/i") ),

			"Other" 	  => array( 
									new MongoRegex("/^((?!Agriculture).)*$/i"), 
									new MongoRegex("/^((?!Education).)*$/i"), 
									new MongoRegex("/^((?!Health).)*$/i"), 
									new MongoRegex("/^((?!Industry).)*$/i"), 
									new MongoRegex("/^((?!Water).)*$/i")
								)
		);

	$option = $sub_options[$sector];

	// $testhandle = fopen("/var/www/html/aiddata/data/form/test.csv", "w");
	// $testhandle2 = fopen("/var/www/html/aiddata/data/form/test2.csv", "w");

	// init mongo
	$m = new MongoClient();
	$db = $m->selectDB($database);
	$col = $db->selectCollection($collection);


	// --------------------
	// generate query

	$query = array();

	// filter (by sector)
	$andor = array();
	if ( $sector != "Other" ) {
		$filter_type = '$or';
		$andor[] = array( $filter => array('$in' => $option) );

	} else {
		$filter_type = '$and';
		foreach ($option as $k => $op) {
			
			$andor[] =  array( $filter => $op );

		}
	}
	$query[] = array( '$match' => array($filter_type => $andor) );
	
	// unwind transactions
	$query[] = array( '$unwind' => '$transactions' );

	// transactions filter (transaction type and year)
	$query[] = array( 
						'$match' => array(
											'transactions.transaction_value_code' => $transaction_type, 
											'transactions.transaction_year' => array( '$gte' => $start_year, '$lte' => $end_year ) 
										)
					);

	// group transactions
	$query[] = array( 
						'$group' => array(  
											'_id' => '$project_id', 
											'project_id' => array( '$last' => '$project_id' ), 
											'is_geocoded' => array( '$last' => '$is_geocoded' ),	
											'project_title' => array( '$last' => '$project_title' ),	
											'start_actual_isodate' => array( '$last' => '$start_actual_isodate' ),	
											'start_actual_type' => array( '$last' => '$start_actual_type' ),	
											'end_actual_isodate' => array( '$last' => '$end_actual_isodate' ),	
											'end_actual_type' => array( '$last' => '$end_actual_type' ),	
											'donors' => array( '$last' => '$donors' ), 
											'donors_iso3' => array( '$last' => '$donors_iso3' ),
											'sector_name_trans' => array( '$last' => '$sector_name_trans' ), 	
											'ad_sector_codes' => array( '$last' => '$ad_sector_codes' ), 
											'ad_sector_names' => array( '$last' => '$ad_sector_names' ),	 
											'status' => array( '$last' => '$status' ), 
											'locations' => array( '$last' => '$locations' ), 
											'total_commitments' => array( '$last' => '$total_commitments' ),	
											'total_disbursements' => array( '$last' => '$total_disbursements' ),
											'transaction_sum' => array( '$sum' => '$transactions.transaction_value' )
										) 
					);

	// unwind locations
	$query[] = array( '$unwind' => '$locations' );

	$query[] = array( 
						'$project' => array(  
											'project_id' => 1, 
											'is_geocoded' => 1,	
											'project_title' => 1,	
											'start_actual_isodate' => 1,	
											'start_actual_type' => 1,	
											'end_actual_isodate' => 1,	
											'end_actual_type' => 1,	
											'donors' => 1, 
											'donors_iso3' => 1,
											'sector_name_trans' => 1, 	
											'ad_sector_codes' => 1, 
											'ad_sector_names' => 1,	 
											'status' => 1, 
											'total_commitments' => 1,	
											'total_disbursements' => 1,
											'transaction_sum' => 1,

											'project_location_id' => '$locations.project_location_id', 
											'precision_code' => '$locations.precision_code', 
											'geoname_id' => '$locations.geoname_id', 
											'place_name' => '$locations.place_name', 
											'latitude' => '$locations.latitude', 
											'longitude' => '$locations.longitude', 
											'location_type_code' => '$locations.location_type_code', 
											'location_type_name' => '$locations.location_type_name', 
											'location_count' => '$locations.location_count',

											'site_commitments' => array( '$divide' => array('$transaction_sum', '$locations.location_count') )

										) 
					);


	// fwrite( $testhandle, json_encode($query) );

	$cursor = $col->aggregate($query);

	// fwrite( $testhandle2, json_encode($cursor) );


	// --------------------
	//build csv if query produced results

	if ( $cursor["result"] && count($cursor["result"]) > 0 ) {

		$filename = "/var/www/html/aiddata/data/form/sector_data/".$database."_".$sector;
		$csv = fopen($filename.".csv", "w");

		$c = 0;
		foreach ($cursor["result"] as $item) {
    	    $row = (array) $item;

    	    $array_values = array_values($row); 

       		array_shift($row);

       		// manage csv header
		 	if ($c == 0) {
		 		$array_keys = array_keys($row);
		    	fputcsv($csv, $array_keys);
		    	$c = 1;
		 	}

		 	// get rid of extra mongo _id field
		 	array_shift($array_values);
		 	
		 	fputcsv($csv, $array_values);
	    }

	    $vrt = '';

		$vrt .= '<OGRVRTDataSource>';
			$vrt .= '<OGRVRTLayer name="'.$database.'_'.$sector.'">';
				$vrt .= '<SrcDataSource relativeToVRT="1">'.$database.'_'.$sector.'.csv</SrcDataSource>';
				$vrt .= '<GeometryType>wkbUnknown</GeometryType>';
				$vrt .= '<GeometryField encoding="PointFromColumns" x="longitude" y="latitude"/>';
			$vrt .= '</OGRVRTLayer>';
		$vrt .= '</OGRVRTDataSource>';

	    file_put_contents($filename.".vrt", $vrt);

		$out = "buildCSV.php : query successful. results in: ".$filename;

	} else {
		$out = "buildCSV.php : no data from query";
	}

	echo $out;

?>
