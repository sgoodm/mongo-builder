<?php

	// /usr/bin/php5 /var/www/html/aiddata/data/form/buildCSV_presenegal.php' country sector

	// --------------------
	// init

	$database = $argv[1];
	$collection = "complete";

	$filter = 'ad_sector_names';
	$sector = $argv[2]; // industry name

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
	
	
	// fwrite( $testhandle, json_encode($query) );

	$cursor = $col->aggregate($query);

	// fwrite( $testhandle2, json_encode($cursor) );


	//build csv if query produced results
	if ( count($cursor["result"]) > 0 ) {

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
