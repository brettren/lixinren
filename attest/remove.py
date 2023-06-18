import re

# Open input file
with open("input.kt", "r") as f:
    input_file = f.read()

# Remove @SFTestAttributeSetup decorator
output_file = re.sub(r'sfuiTestcaseAttributes.SFTestAttributeSetup\(.*?\)\n', '', input_file)

# Write output file
with open("output.kt", "w") as f:
    f.write(output_file)
