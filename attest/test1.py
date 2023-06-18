import re
import os


def move(fileName):
    # Open the input file
    with open(fileName, "r") as input_file:
        try:
            input_text = input_file.read()
        except:
            print(fileName)

    # Define the regular expression pattern to match
    # pattern = r"(\s*fun\s+(.*)\{\n)(^\s*sfuiTestcaseAttributes\.SFTestAttributeSetup\(\n^(.+)$\n^(.+)$\n^(.+)$\n^(.+)$\n^(.+)$\n^(.+)$\n^(.+)$\n^(.+)$\n^(.+)$\n^(.+)$\n\s+\)\n)"
    pattern = r'(\s*fun(.*)\{\n)(.*\n)(\s*sfuiTestcaseAttributes.SFTestAttributeSetup\(\n(.+)\n(.+)\n(.+)\n(.+)\n(.+)\n(.+)\n(.+)\n(.+)\n(.+)\n(.+)\n(.+)\n(.+)\n(.+)\n(.+)\n(.+)\n(.+)\n(.+)\n(.+)\n(.+)\n(.+)\n(.+)\n\s+\)\n)'

    # Find all matches of the pattern in the input text
    matches = re.findall(pattern, input_text)

    # Process each match
    for match in matches:
        # Extract the start, middle, and end parts of the match
        start = match[0][2:-1]
        middle = match[2]
        middle = middle[0:-1]
        end = match[3][0:-1].replace("    sfuiTestcaseAttributes.SFTestAttributeSetup", "@SFTestAttribute")
        end = end.replace("        ", "    ")
        end = re.sub(r"\s*data(.*),", "", end)
        # Construct the new text with the swapped lines
        new_text = f"\n{end}\n{start}\n{middle}\n"

        # Replace the old text with the new text in the input text
        input_text = re.sub(pattern, new_text, input_text, 1)

    # Write the modified text back to the original file
    with open(fileName, "w") as output_file:
        output_file.write(input_text)


def add(fileName):
    # Open the input file
    with open(fileName, "r") as input_file:
        try:
            input_text = input_file.read()
        except:
            print(fileName)
    value = "import com.successfactors.android.annotations.SFTestAttribute"
    if value not in input_text:
        input_text = input_text.replace("import com.successfactors.android.annotations.TestLinkId",
                                        f"import com.successfactors.android.annotations.TestLinkId\nimport com.successfactors.android.annotations.SFTestAttribute")
        # Write the modified text back to the original file
        with open(fileName, "w") as output_file:
            output_file.write(input_text)


filepath = "/Users/i336543/Documents/SuccessFactors_App/androidrepo/uiautomator/src/uiautomator"
for root, directories, filenames in os.walk(filepath):
    for filename in filenames:
        filepath = root + os.sep + filename
        if filepath.endswith("kt"):
            add(filepath)
