Step 1. Get data on samples with  known and unique Stages, and unique Disease type

python pdc_discovery_scripts/main.py

This generates the "unambiguous_file_metadata_with_urls.csv" file under ./wd.

Step 2. Filter by cancer stages

python filter_by_stage.py

This generates data_noninvasive.csv and data_invasive.csv files.

Step 3. Download and process .mzid.gz data files

python process_manifest_file.py

This generates two folders, noninvasive_protein_list and invasive_protein_list, with multiple txt files in it.

Step 4. Count proteins in txt files

python write_to_csv.py

This generates protein_summary.csv.
It writes the proteins and its detials to a csv that we can use.

Step 5. Use Cytoscape to process the data from protein_summary.csv
