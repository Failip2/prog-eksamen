import pickle
import os
DEFAULT_DATA = {("Highscore", 0)}

#Save data array to filepath
def saveData(path_to_file, array):
    with open(path_to_file, 'wb') as file:
        pickle.dump(array, file)
    print("Saved Data")

#Read data from .pickle -> data
def getRawData(path_to_file, defaultData=DEFAULT_DATA):
    if not is_non_zero_file(path_to_file):
        print("No Data Found, writing default data")
        clearData(path_to_file)

    with open(path_to_file, 'rb') as file:
    # Deserialize and retrieve the variable from the file
        data = pickle.load(file)
        print(f"Data Loaded: {data}")
        return data

#Clear Data by saving data as default array
def clearData(path_to_file, defaultData=DEFAULT_DATA):
    saveData(path_to_file, defaultData)

#Check if file exists and is written more than 0 bytes
def is_non_zero_file(path_to_file):  
    return os.path.isfile(path_to_file) and os.path.getsize(path_to_file) > 0