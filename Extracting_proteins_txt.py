import pandas as pd

def extracting_protiens(protiens_csv_file):
    df = pd.read_csv('protein_summary.csv')

    required_collums_fromcsv = df[['protein name', 'invasive counts', 'non-invasive counts']]
    if not all(col in df.columns for col in required_collums_fromcsv):
        raise ValueError("The columns in the CSV file are not as expected")

    invasive_proteins = df[df["invasive counts"] > 0]["protein name"].tolist()
    non_invasive_proteins = df[df["non-invasive counts"] > 0]["protein name"].tolist()

    with open('invasive_proteins.txt', 'w') as f:
        f.write("\n".join(invasive_proteins))
    with open('non_invasive_proteins.txt','w') as f:
        f.write("\n".join(non_invasive_proteins))

    print (f"extracted invasive proteins: {len(invasive_proteins)} and non-invasive proteins: {len(non_invasive_proteins)}")

extracting_protiens("/Users/sathvikshivaram/CourseProject/protein_summary.csv")