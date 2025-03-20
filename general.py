import os


def getAllFilesInDir(DIRECTORY_PATH, FILE_ENDING):
    arr = []
    for filename in os.listdir(DIRECTORY_PATH):
        f = os.path.join(DIRECTORY_PATH, filename)

        if os.path.isfile(f) and f.endswith(FILE_ENDING):
            arr.append(f)
    return arr