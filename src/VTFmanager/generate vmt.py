import json

# SETS THE PARENT DIR TO SRC FOLDER
import sys
import os
import argparse
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import re
import difflib
from lib import SMDpraser as praser

# Paths
tmp_dir = r"D:\programs\source engine utils\test_files"
CONFIG = os.path.join(os.path.dirname(__file__), 'config', 'vtf_suffix_matching.json')
# gets the material suffix from config


# config manager
class ConfigManager:
    def __init__(self, path=CONFIG):
        self.path = path
        self.config = self._load()

    def _load(self):
        if not os.path.exists(self.path):
            return {"template_path": "", "suffix_mappings": {}}
        with open(self.path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def save(self):
        with open(self.path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=4)

    def get_suffix_map(self):
        # Return only the suffix mappings dictionary
        return self.config.get("suffix_mappings", {})

    def get_template_path(self):
        return self.config.get("template_path", "")

    def set_template_path(self, path):
        self.config["template_path"] = path

    def add_suffix(self, key, suffix):
        self.config.setdefault("suffix_mappings", {}).setdefault(key, [])
        if suffix not in self.config["suffix_mappings"][key]:
            self.config["suffix_mappings"][key].append(suffix)

    def remove_suffix(self, key, suffix):
        if key in self.config["suffix_mappings"]:
            self.config["suffix_mappings"][key] = [s for s in self.config["suffix_mappings"][key] if s != suffix]
    
    def get_material_suffix(self):
        return self.config.get('material_suffix_templates', {})

    # grabs the correct template file for the material suffix
    # templates are loaded in config\template
    def grab_template_for_material(self, material_name):
        suffix_map = self.get_material_suffix()
        for suffix, r_path in suffix_map.items():
            if material_name.lower().endswith(suffix.lower()):
                abs_path = os.path.normpath(os.path.join(os.path.dirname(self.path), r_path)) 
                print ('')
                
                # OLD: this doesnt trigger? means its not file then but why?
                # it was because this loads it in the config folder. my template folder was outside of the config
                if os.path.isfile(abs_path):
                    #print('Suffix Template Path : ' + abs_path)
                    return abs_path
                else:
                    pass
                    #print('failed os.path.isfile - ' + abs_path)
        return self.get_template_path()

# -------------------------------------------
#               Function Logic
# -------------------------------------------

# validates the sfm material input
# it check if a real path on system, if ends with materials, if folder one level up is named game
def valid_materials_path(path):
    path = os.path.normpath(path)
    parent_folder = os.path.basename(os.path.dirname(path))
    if not os.path.isdir(path) or os.path.basename(path).lower() != "materials" or parent_folder.lower() == "game":
        return False
    return True

# scans qcs and grab the $cdmaterials path 
def get_cdmaterials(path):
    cdmaterials_list = set()
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.lower().endswith('.qc'):
                abs_path = os.path.join(root, file)
                with open(abs_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    matches = re.findall(r'\$cdmaterials\s+"([^"]+)"', content, re.IGNORECASE)
                    for match in matches:
                        cdmaterials_list.add(match)
    return cdmaterials_list

def get_cdmaterials_multiple(paths):
    cdmaterials = set()
    for path in paths:
        cdmaterials.update(get_cdmaterials(path))
    return cdmaterials

# scans qcs and extract smds used in qc. ($model, $body, $bodygroup studio)
def get_smds(path):
    SMD_PATTERNS = [
        re.compile(r'\$model\s+\S+\s+"([\w\s\\.-]+\.smd)"', re.IGNORECASE),
        re.compile(r'\$body\s+\S+\s+"([\w\s\\.-]+\.smd)"', re.IGNORECASE),
        re.compile(r'studio\s+"([\w\s\\.-]+\.smd)"', re.IGNORECASE),
    ]
    smd_files = set()
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.lower().endswith('.qc'):
                abs_path = os.path.join(root, file)
                with open(abs_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                for pattern in SMD_PATTERNS:
                    matches = pattern.findall(content)
                    for match in matches:
                        smd_files.add(os.path.normpath(os.path.join(root, match)))
    return smd_files

# scans vtfs, returns vtf name and vtf cdmat path 
def collect_vtf(scan_path, materials_root):
    vtf_files = []
    for root, _, files in os.walk(scan_path):
        for file in files:
            if file.lower().endswith('.vtf'):
                rm_ext = os.path.splitext(file)[0].lower()
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, materials_root)
                vtf_files.append((rm_ext, rel_path.replace("\\", "/")))
    return vtf_files

# scans for parmaters in config. matches suffix to parameters and matches textures to materials
def map_vtfs_to_keys_per_material(material_name, vtf_list, key_to_suffixes, cutoff=0.6):
    # Extract base names (e.g. ak4_sight_color -> ak4_sight)
    vtf_basenames = list(set(name.rsplit('_', 1)[0] for name, _ in vtf_list if '_' in name))
    matches = difflib.get_close_matches(material_name.lower(), vtf_basenames, n=1, cutoff=cutoff)
    if not matches:
        return {}
    matched_prefix = matches[0]
    filtered_vtfs = [(name, path) for name, path in vtf_list if name.startswith(matched_prefix)]
    mapped = {}
    for vtf_name, vtf_path in filtered_vtfs:
        for key, suffixes in key_to_suffixes.items():
            if any(vtf_name.endswith(suffix) for suffix in suffixes):
                mapped[key] = vtf_path
                break
    return mapped

# file list interperter
def parse_filelist(path):
    input_paths = []
    materials_path = None

    if not os.path.isfile(path):
        print(f"File list not found: {path}")
        sys.exit(1)

    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            if '=' not in line:
                print(f"Invalid line in file list: {line}")
                continue

            key, _, raw_value = line.partition('=')
            key = key.strip().lower()
            value = raw_value.strip().strip('"').strip("'")

            if not value:
                print(f"Empty path for {key} in file list.")
                continue

            if key == 'input':
                input_paths.append(os.path.normpath(value))
            elif key == 'materials':
                if materials_path is not None:
                    print("Error: Only one 'materials=' entry is allowed in the file list.")
                    sys.exit(1)
                materials_path = os.path.normpath(value)
            else:
                print(f"Unknown key in file list: {key}")

    if materials_path is None:
        print("Error: Missing 'materials=' entry in file list.")
        sys.exit(1)

    return input_paths, materials_path

# -------------------------------------------------------------------------------------------

# ---------------------------------------------
#               Execution logic
# ---------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="SMD to VMT Generator CLI")
    parser.add_argument('--input', '-i', action='append', help='Path to QC/SMD files (can be used multiple times)')
    parser.add_argument('--materials', '-m', help='Path to SFM materials folder')
    parser.add_argument('--filelist', '-l', help='Path to file list containing input/materials paths')
    parser.add_argument('--config', '-c', action='store_true', help='Launch config editor')
    args = parser.parse_args()

    if args.config:
        run_config_editor()
        return

    input_paths = args.input or []
    materials_path = args.materials

    if args.filelist:
        file_inputs, file_materials = parse_filelist(args.filelist)
        input_paths.extend(file_inputs)
        materials_path = file_materials  # override

    if not input_paths or not materials_path:
        parser.error("You must provide at least one --input and one --materials path, or use --filelist")

    if not valid_materials_path(materials_path):
        print("Invalid materials path provided.")
        sys.exit(1)

    config_manager = ConfigManager()
    key_to_suffixes = config_manager.get_suffix_map()

    smd_materials = set()
    for path in input_paths:
        for smds in sorted(get_smds(path)):
            smd = praser.SMDFile(smds)
            smd_materials.update(smd.materials)

    for mat in smd_materials:
        for path in sorted(get_cdmaterials_multiple(input_paths)):
            normalize_vmt_path = os.path.normpath(os.path.join(materials_path, path))
            write_vmt = os.path.join(normalize_vmt_path, f"{mat}.vmt")

            vtf_list = collect_vtf(normalize_vmt_path, materials_path)
            mapped_textures = map_vtfs_to_keys_per_material(mat, vtf_list, key_to_suffixes)

            print('Material : \n ' + mat + '\n')
            # Select the right template for this material based on suffix
            template_path = config_manager.grab_template_for_material(mat)
            print(template_path)

            if not os.path.isfile(template_path):
                print(f"VMT template not found at {template_path} for material {mat}")
                continue

            with open(template_path, 'r', errors='ignore') as f:
                vmt_content = f.readlines()

            print(f"Writing VMT: {write_vmt}")
            os.makedirs(os.path.dirname(write_vmt), exist_ok=True)

            vmt_output = []
            for line in vmt_content:
                new_line = line
                for vmt_key, vtf_path in mapped_textures.items():
                    rel_path = vtf_path.replace("\\", "/")
                    rel_path_no_ext = os.path.splitext(rel_path)[0]
                    placeholder = f"%{vmt_key.strip('$')}%"
                    new_line = new_line.replace(placeholder, rel_path_no_ext)

                # Strip remaining placeholders
                for key in key_to_suffixes.keys():
                    placeholder = f"%{key.strip('$')}%"
                    if placeholder in new_line:
                        new_line = new_line.replace(placeholder, '')

                vmt_output.append(new_line)

            with open(write_vmt, "w", encoding="utf-8", errors='ignore') as f:
                f.writelines(vmt_output)

def run_config_editor():
    manager = ConfigManager()

    def show_menu():
        print("\n--- CONFIG EDITOR ---")
        print("1. View Config")
        print("2. Set VMT Template Path")
        print("3. Add Suffix to Key")
        print("4. Remove Suffix from Key")
        print("5. Save and Exit")

    while True:
        show_menu()
        choice = input("Select an option: ").strip()
        if choice == '1':
            print(json.dumps(manager.config, indent=4))
        elif choice == '2':
            new_path = input("Enter new template path: ").strip()
            manager.set_template_path(new_path)
        elif choice == '3':
            key = input("Enter VMT key (e.g. $basetexture): ").strip()
            suffix = input("Enter suffix (e.g. _color): ").strip()
            manager.add_suffix(key, suffix)
        elif choice == '4':
            key = input("Enter VMT key: ").strip()
            suffix = input("Enter suffix to remove: ").strip()
            manager.remove_suffix(key, suffix)
        elif choice == '5':
            manager.save()
            print("Config saved.")
            break
        else:
            print("Invalid option.")

if __name__ == '__main__':
    main()

# ---------------------------------------------------------------------------------------------