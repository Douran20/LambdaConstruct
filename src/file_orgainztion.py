import os
import shutil

# Set your directory here
TARGET_DIRECTORY = r"D:\models\scp\weapons\FR-MG-0\textures"

# Define suffixes and their corresponding folders
SUFFIX_TO_FOLDER = {
    "AlbedoTransparency.png": "Color",
    "BaseColor.png": "Color",
    "Albedo.png": "Color",
    "Mask.png" : "masks",
    "maskmap.png": "masks",
    "normal.png": "Normal",
}

def move_files_by_suffix_map(directory, suffix_map):
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if not os.path.isfile(file_path):
            continue

        for suffix, folder_name in suffix_map.items():
            if filename.lower().endswith(suffix.lower()):
                dest_folder = os.path.join(directory, folder_name)
                os.makedirs(dest_folder, exist_ok=True)
                shutil.move(file_path, os.path.join(dest_folder, filename))
                print(f"Moved {filename} → {dest_folder}")
                break  # Skip checking other suffixes after a match

if __name__ == "__main__":
    if os.path.isdir(TARGET_DIRECTORY):
        move_files_by_suffix_map(TARGET_DIRECTORY, SUFFIX_TO_FOLDER)
        print("All matching files have been organized.")
    else:
        print("Invalid directory path. Please update TARGET_DIRECTORY.")
