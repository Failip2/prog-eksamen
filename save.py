# Filip har skrevet dette - meget inspiration fra et tidligere programmerings projekt

import pickle
import os

# Default data to be used if no existing data is found
DEFAULT_DATA = {("Highscore", 0)}

# Save data array to the specified file path
# This function serializes the given array and writes it to a file using pickle
def saveData(path_to_file, array):
    with open(path_to_file, 'wb') as file:
        pickle.dump(array, file)
    print("Saved Data")

# Read data from a .pickle file and return it
# If the file does not exist or is empty, write default data to the file
def getRawData(path_to_file, defaultData=DEFAULT_DATA):
    if not is_non_zero_file(path_to_file):
        print("No Data Found, writing default data")
        clearData(path_to_file)

    with open(path_to_file, 'rb') as file:
        # Deserialize and retrieve the variable from the file
        data = pickle.load(file)
        print(f"Data Loaded: {data}")
        return data

# Clear data by saving the default data array to the specified file path
# This function is used to reset the data to its default state
def clearData(path_to_file, defaultData=DEFAULT_DATA):
    saveData(path_to_file, defaultData)

# Check if the file exists and is non-zero in size
# This function is used to determine if the file contains any data
def is_non_zero_file(path_to_file):  
    return os.path.isfile(path_to_file) and os.path.getsize(path_to_file) > 0