from pyteomics import mzid
with mzid.MzIdentML("input.mzid") as f:
    proteins = set()
    for spectrum in f:
        try:
            protein = spectrum['SpectrumIdentificationItem'][0]['PeptideEvidenceRef'][0]['protein description']
            proteins.add(protein)
        except:
            pass
 
for protein in proteins:
    print(protein)
