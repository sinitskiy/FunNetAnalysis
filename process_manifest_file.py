import os
import csv
import requests
import shutil
import gzip
from pyteomics import mzid

MANIFEST_FILE = 'ColonorRectumAdenocarcinomaStageIII.csv'
DOWNLOAD_DIR = 'downloaded_files'
EXTRACTED_DIR = 'extracted_files'
PROTEIN_LIST_DIR = 'StageIII_protein_list'

os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(EXTRACTED_DIR, exist_ok=True)
os.makedirs(PROTEIN_LIST_DIR, exist_ok=True)

PROBLEMATIC_LIST_FILE = 'stageiii_problematic_files.txt'

problematic_files = []

def download_file(url, local_filename):
    """
    Download a file from the given URL and save it as local_filename.
    """
    with requests.get(url, stream=True) as response:
        response.raise_for_status()
        with open(local_filename, 'wb') as out_file:
            shutil.copyfileobj(response.raw, out_file)
    return local_filename

def extract_gz_file(gz_path, extracted_folder):
    """
    Extract a .gz file into the specified extracted_folder.
    The extracted file will have the same name as gz_path but without the .gz extension.
    """
    base_filename = os.path.basename(gz_path)
    if base_filename.endswith('.gz'):
        extracted_filename = base_filename[:-3]
    else:
        extracted_filename = base_filename
    extracted_path = os.path.join(extracted_folder, extracted_filename)
    with gzip.open(gz_path, 'rb') as f_in, open(extracted_path, 'wb') as f_out:
        shutil.copyfileobj(f_in, f_out)
    return extracted_path

def extract_proteins(mzid_path):
    """
    Extract protein names from an mzid file using pyteomics.
    Returns a set of protein names.
    """
    proteins = set()
    try:
        with mzid.MzIdentML(mzid_path) as reader:
            for spectrum in reader:
                try:
                    protein = spectrum['SpectrumIdentificationItem'][0]['PeptideEvidenceRef'][0]['protein description']
                    proteins.add(protein)
                except Exception:
                    # Skip any spectrum that doesn't have the expected structure.
                    pass
    except Exception as e:
        print(f"Error reading {mzid_path}: {e}")
    return proteins

with open(MANIFEST_FILE, 'r', newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        print(f"Processing row: {row}")
        file_url = row.get('File Download Link')
        if not file_url:
            print("No 'File Download Link' found; skipping row.")
            continue

        # Use 'File Name' if available; else derive from URL.
        file_name = row.get('file_name') or os.path.basename(file_url.split('?')[0])
        base_name = os.path.splitext(file_name)[0]  # removes extension (e.g., .mzid.gz)

        # Check if protein list already exists (to avoid redoing work).
        protein_list_file = os.path.join(PROTEIN_LIST_DIR, base_name + '.txt')
        if os.path.exists(protein_list_file):
            print(f"Protein list for {file_name} already exists; skipping processing.")
            continue

        # Download the .mzid.gz file into DOWNLOAD_DIR.
        gz_path = os.path.join(DOWNLOAD_DIR, file_name)
        try:
            print(f"Downloading {file_url} into {gz_path} ...")
            download_file(file_url, gz_path)
            print("Download complete.")
        except Exception as e:
            print(f"Failed to download {file_url}: {e}")
            continue

        # Unzip the .gz file into EXTRACTED_DIR.
        try:
            extracted_path = extract_gz_file(gz_path, EXTRACTED_DIR)
            print(f"Extracted {gz_path} to {extracted_path}")
        except Exception as e:
            print(f"Failed to extract {gz_path}: {e}")
            continue

        # Extract protein names from the unzipped .mzid file.
        protein_names = extract_proteins(extracted_path)
        protein_count = len(protein_names)
        print(f"Extracted {len(protein_names)} proteins from {extracted_path}")

        # Save protein names to protein_list_file (one per line).
        try:
            with open(protein_list_file, 'w') as f:
                for protein in protein_names:
                    f.write(protein + '\n')
            print(f"Saved protein names to {protein_list_file}")
        except Exception as e:
            print(f"Error writing to {protein_list_file}: {e}")

        # If number of proteins > 100, record this file as problematic.
        
        is_problematic = protein_count < 300
        if is_problematic:
            print(f"Problematic file detected: {file_name} has only {protein_count} proteins.")
            problematic_files.append((file_name, protein_count, file_url))
            problematic_files.sort(key=lambda x: x[1])
            print("Sorted problematic file list so far:")
            for fname, count, url in problematic_files:
                print(f"{fname}: {count} proteins, {url}") 
            with open(PROBLEMATIC_LIST_FILE, 'w') as pf:
                for fname, count, url in problematic_files:
                    pf.write(f"{fname}: {count}\n, URL: {url}\n")
        

        # Delete the downloaded and extracted files.
        try:
            if os.path.exists(gz_path):
                os.remove(gz_path)
                print(f"Deleted downloaded file {gz_path}")
            # Delete the extracted file only if not problematic.
            if os.path.exists(extracted_path):
                os.remove(extracted_path)
                print(f"Deleted extracted file {extracted_path}")
            """
            if not is_problematic and os.path.exists(extracted_path):
                os.remove(extracted_path)
                print(f"Deleted extracted file {extracted_path}")
            elif is_problematic:
                print(f"Kept extracted file {extracted_path} for review (problematic file).")
            """
        except Exception as e:
            print(f"Error deleting files: {e}")

        print("-" * 40)