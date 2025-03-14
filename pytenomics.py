import csv
from pyteomics import mzid
def extract_proteins_frommzid(mzid_path):
     proteins_set = set()

     with mzid.MzIdentML(mzid_path) as f:
          for spectrum in f:
               try:
                  for item in spectrum.get('SpectrumIdentificationItem',[]):
                      for Pepevidence in item.get('PeptideEvidenceRef',[]):
                          protein = Pepevidence.get('protein description', None)
                          if protein:
                              proteins_set.add(protein)
               except Exception as e:
                   print(f"Error processing spectrum: {e}")
     return proteins_set

def save_to_csv_and_txt(proteins, csv_path, txt_path):
     with open(csv_path, mode='w', newline='') as csv_file:
       writer = csv.writer(csv_file)
       writer.writerow(['Protein Name'])  # CSV header
       for protein in proteins:
            writer.writerow([protein])    

     with open(txt_path, mode='w') as txt_file:
          for protein in proteins:
            txt_file.write(f"{protein}\n") 


mzid_path = "C:\Genomeclass\extracted\JK082219_121619_PTRC_Ov_FFPE_Gr11_TMT_11plex_bRP_GLBL_F20_Run2.mzid"
proteins = extract_proteins_frommzid(mzid_path)

csv_file ="proteins.csv"
txt_file = "proteins.txt"

save_to_csv_and_txt(proteins, csv_file,txt_file)
for protein in proteins:
    print(protein)

print(f"Proteins saved to {csv_file} and {txt_file}")