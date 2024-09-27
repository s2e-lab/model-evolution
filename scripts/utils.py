import os
import shutil
import sys


def delete_folder(folder_location: str) -> bool:
    """
    Delete a folder and its contents.
    :param folder_location: the location of the folder to be deleted.
    :return: True if the folder was deleted (ie, it no longer exist), False otherwise.
    """
    shutil.rmtree(folder_location, ignore_errors=True)

    # check if the folder still exists
    if os.path.exists(folder_location):
        current_os = sys.platform.system()
        if current_os == "Windows": # Use rmdir for Windows
            os.system(f'rmdir /S /Q "{folder_location}"')
        else: # Use rm -rf for Linux/macOS
            os.system(f'rm -rf {folder_location}')
    return not os.path.exists(folder_location)
