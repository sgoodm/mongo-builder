<?php

	//combine individual extract output files into one file 

	$country = $argv[1];
	$sector = $argv[2];

	// open files
	$base = '/var/www/html/aiddata/data/form/extract_data/'.$country.'_'.$sector;
	$handles = array();
		$handles[0] = fopen( $base . "_Yield.csv", "r" ); 
		$handles[1] = fopen( $base . "_Income.csv", "r" ); 
		$handles[2] = fopen( $base . "_Urban.csv", "r" ); 
	$outHandle = fopen('/var/www/html/aiddata/data/form/form_data/'.$country.'_'.$sector.'.csv', "w");

	// join files
	while ($fRow = fgetcsv($handles[0])){
		$outRow = $fRow;
		for ($i=1; $i<count($handles); $i++){
			$outRow[] = fgetcsv($handles[$i])[count($fRow)-1];
		}
		fwrite($outHandle, implode($outRow, ",")."\n");
	}

	// close files
	for ($i=0; $i<3; $i++) {		
		fclose( $handles[$i] );
	}
	fclose($outHandle);

	echo "joinExtract.php : done";

?>
