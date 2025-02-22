import pandas as pd

# Read the comma-separated CSV file into a pandas DataFrame
# Replace 'your_file.csv' with the actual path to your CSV file
df = pd.read_csv('eto.csv')  # Ensure your file path is correct

# Open a text file to write the output
with open('output_formulas.txt', 'w') as f:
    # Start writing the formula for the first condition
    for i, row in df.iterrows():
        # Extract the 'Identifier' and 'Phone Number' columns
        identifier = row['Identifier']
        phone_number = row['Phone Number']
        
        # If the phone number is empty or NaN, we leave it blank in the formula
        if pd.isna(phone_number) or phone_number == "":
            phone_number = ""  # Leave the phone number blank in the formula
        
        # Write the formula for the current row to the text file
        if i == 0:
            f.write(f'=If([Employer_68] InList({identifier})) Then "{phone_number}"\n')
        else:
            f.write(f'ElseIf([Employer_68] InList({identifier})) Then "{phone_number}"\n')
        
    # Write a closing Else for unknown identifiers
    f.write('Else "Unknown"\n')

print("Formulas have been written to 'output_formulas.txt'")
