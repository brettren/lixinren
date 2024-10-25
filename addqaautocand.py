import os
import json
import copy

# Get the path to the json directory
dir_path = '/Users/i336543/SAPDevelop/androidrepo/uiautomator/src/uiautomator/assets/json'

# Walk through all files in the directory
for root, dirs, files in os.walk(dir_path):
    for file in files:
        # Check if the file is a .json file
        if file.endswith('.json'):
            file_path = os.path.join(root, file)
            # Load the data from the JSON file
            with open(file_path, 'r') as f:
                data = json.load(f)

            # Check if "qapatchpreview" is in the data
            if 'qaautocand' in data:
                # Copy the object
                # qapatchpreview_copy = copy.deepcopy(data['qapatchpreview'])

                # Add another object "qaautocand" with the same content
                for value in data['qaautocand']:
                    value['serverName'] = 'qaautocand'

            # Write the data back to the JSON file
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
