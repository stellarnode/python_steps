import os

def rename_files():
    file_list = os.listdir(r"/users/filmmaker/desktop/python/prank/")
    print(file_list)

    path = os.getcwd()
    os.chdir(r"/users/filmmaker/desktop/python/prank/")
    
    for file_name in file_list:
        print("old file name: " + file_name)
        print("new file name: " + file_name.translate(None, "0123456789"))
        os.rename(file_name, file_name.translate(None, "0123456789"))

    os.chdir(path)

rename_files()
