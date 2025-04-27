import os
import re
import csv
from collections import defaultdict

protein_regex = r"\|([A-Z0-9_]+)_HUMAN"

def process_txt(txt_folder_path):

    if not os.path.isdir(txt_folder_path):
        raise NotADirectoryError(f"Error: Provided path '{txt_folder_path}' is not a directory.") 
    files = [f for f in os.listdir(txt_folder_path) if f.endswith('.txt') and os.path.isfile(os.path.join(txt_folder_path, f))]
    if not files:
        raise FileNotFoundError(f"No .txt files found in the directory: {txt_folder_path}")
    
    proteins_counts = defaultdict(int)
    tracking_total_files = 0
    
    for filename in files:
        txt_file_path = os.path.join(txt_folder_path, filename)

        print(f"Processing file: {txt_file_path}")
        tracking_total_files += 1
            
        try:
            with open(txt_file_path, 'r', encoding='utf-8') as f:
                proteins_inthe_file = set()
                for pline in f:
                    match = re.search(protein_regex, pline.strip())
                    if match:
                        protein_id = match.group(1)
                        proteins_inthe_file.add(protein_id)     
        except Exception as e:
            print(f"error reading file {txt_file_path}: {e}")
            continue
        
        for protein in proteins_inthe_file:
            proteins_counts[protein] +=1 
            
    print(f"Total files processed: {tracking_total_files}")
    return proteins_counts, tracking_total_files 


def write_to_csv(inv_counts, invasive_total, non_inv_counts, non_invasive_total, output_file):
    all_proteins = set(inv_counts.keys()).union(set(non_inv_counts.keys()))
    with open(output_file, 'w', newline='') as csvfile:
        writer_to_csv = csv.writer(csvfile)
        writer_to_csv.writerow([
            "protein name", 
            # "total count", "total fraction", 
            "invasive counts", "invasive fraction", 
            "non-invasive counts", "non-invasive fraction"
        ])

        for protein in all_proteins:
          
            invasive_count = inv_counts.get(protein, 0)
            non_invasive_count = non_inv_counts.get(protein, 0)
            total_count = invasive_count + non_invasive_count
            total_files = invasive_total + non_invasive_total  # All files combined

            total_fraction = total_count / total_files if total_files > 0 else 0
            invasive_fraction = invasive_count / invasive_total if invasive_total > 0 else 0
            non_invasive_fraction = non_invasive_count / non_invasive_total if non_invasive_total > 0 else 0

            writer_to_csv.writerow([
                protein, 
                # total_count, round(total_fraction, 5), 
                invasive_count, round(invasive_fraction, 5), 
                non_invasive_count, round(non_invasive_fraction, 5)
            ])


if __name__ == '__main__':
    stageIII_folder = "./noninvasive_protein_list"
    stageI_folder = "./noninvasive_protein_list"
    output_csv = "./protein_summary.csv"
    
    try:
        inv_counts, invasive_total = process_txt(stageIII_folder)
        non_inv_counts, non_invasive_total = process_txt(stageI_folder)
        write_to_csv(inv_counts, invasive_total, non_inv_counts, non_invasive_total, output_csv)
        print(f"Csv output '{output_csv}' written successfully.")
    except Exception as e:
        print(f"Error: {e}")
