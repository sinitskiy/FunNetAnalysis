## NunNet Project Overview

The purpose of this repository is to streamline the retrieval and analysis of protien-related information from the [Proteomic Data Commons](https://proteomic.datacommons.cancer.gov/pdc/) (PDC) database. These scrips allow users to filter by certain categories, retrieve and store the metadata in a CSV file, download and extract the protein names of each data files, record any problematic files, and count each protein name for occurrences. There will be multiple CSV files generated and the final output is a CSV file with protein counts and fractions. 

## Prerequisites

Ensure you have Python installed. No other dependencies are required. 

## Usage

**Step 1** Generate CSV files base on chosen and unique Stages, and unique Disease type. 

Run `pdc_discovery_scripts/main.py`.

This generates the `unambiguous_file_metadata_with_urls.csv` file under the folder `./wd` which contains download links.

Example of output CSV:

| file_id  |file_name|file_location|pdc_study_id|disease_type|tumor_stage|download_url|
| -------- |:-------:|:-----------:|:----------:|:----------:|:---------:|:----------:|
|0019dd1...|TCGA-A...|studies/11...|PDC000111   |Colon Ade...|Stage IIA  |https://d...|

**Step 2** You can separate the generated CSV file by cancer stages. 

Run `filter_by_stage.py` .

This generates CSV files for `data_noninvasive.csv` and `data_invasive.csv` files.

**Step 3** Download and process .mzid.gz data files and extract protein names in txt files.

Run `process_manifest_file.py`. 

- It generates two folders, `noninvasive_protein_list` and `invasive_protein_list`, with multiple txt files in it. 

- Each txt file is named as the downloaded data file and contain lists of protein names. 

- Files recorded as problematic files will **not** be deleted and will be stored inside `extracted files` folder. 

**Step 4** Count each protein name in all txt files.

Run `write_to_csv.py`.

This generates protein_summary.csv.

Example of output: 
| protein name  |invasive counts|invasive fraction|non-invasive counts|non-invasive fraction|
| ------------- |:-------------:|:---------------:|:-----------------:|:-------------------:|
| A8MXR0        | 33            | 0.05046         | 18                | 0.0625              |

It counts the protein names and related fraction in related stages to a csv that you can use.

**Step 5(optional)** You can use Cytoscape to process the data from protein_summary.csv. 

## Configs to adjust
Inside `all_file_metadata.py`, look for:
```bash
    fileMetadata(
        data_category: "Peptide Spectral Matches"
        file_type: "Open Standard"
        file_format: "mzIdentML"
        offset: {offset}
        limit: 25000
    ) 
```
You can override these fields base on the existing categories on PDC databse:
- `data_category`
- `file_type`
- `file_format`

Remember to modify related fields inside `files_per_study.py` as well in order for the script to generate download links: 
```bash
    filesPerStudy(
        pdc_study_id:  "{pdc_study_id}"
        data_category: "Peptide Spectral Matches"
        file_type:     "Open Standard"
        file_format:   "mzIdentML"
        limit:         25000
    )
```
In `studies_per_disease.py`, you can specify a `{disease type}` shown on PDC database:
```bash
programsProjectsStudies(disease_type: "{disease_type}") {
    projects {
        studies {
        pdc_study_id
        }
```
You can determine which files get stored in the problematic file list by adjusting this value: 
```bash
    is_problematic = protein_count < 300
```

## Known Issue

When you run `main.py` and the terminal returns `httpx.ReadTimeout`, find the following command inside `main.py`:
```bash
    async with httpx.AsyncClient(
        timeout=10,
        transport=transport,
    )
```
You should try changing it to: 

```bash
    async with httpx.AsyncClient(
        timeout=httpx.Timeout(60.0, connect=20.0),
        transport=transport,
    )
```

The current version of `write_to_csv.py` will skip certain format of protein names extracted from the data files. 
