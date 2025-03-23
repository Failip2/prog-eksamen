# Filip har skrevet dette - fra et tidligere programmerings projekt

import os

# Function to get all files in a directory with a specific file ending
# This function scans the given directory and returns a list of file paths that match the specified file ending
def getAllFilesInDir(DIRECTORY_PATH, FILE_ENDING):
    arr = []
    # Iterate over all items in the directory
    for filename in os.listdir(DIRECTORY_PATH):
        # Construct the full file path
        f = os.path.join(DIRECTORY_PATH, filename)

        # Check if the item is a file and if it ends with the specified file ending
        if os.path.isfile(f) and f.endswith(FILE_ENDING):
            # Add the file path to the list
            arr.append(f)
    # Return the list of matching file paths
    return arr