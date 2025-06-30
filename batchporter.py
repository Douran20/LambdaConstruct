import json

import glob
import os
import subprocess

import re
from rapidfuzz import fuzz
import shutil

from prompt_toolkit.shortcuts import button_dialog
from prompt_toolkit.styles import Style

import questionary

def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')

dark_mode_style = Style.from_dict({
    'dialog': 'bg:#111823', 
    'frame.label': 'bg:#18222d #add8e6 bold',                                                
    'dialog.body': 'bg:#18222d #b4cadf',            
    'dialog.frame.border': 'fg:#b4cadf',            
    'button': 'bg:#18222d #b4cadf',                 
    'button.focused': 'bg:#00afaf #a2c8ec',         
    'button-arrow': 'bg:#3c3c3c #ffffff',
    'button-arrow.focused': 'bg:#00afaf #000000',
})

CONFIG_FILE = 'lambdaConstruct.json'

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {
        'studiomdl_path': '',
        'game_dir': '',
        'use_verbose': True,
        'use_nop4': True,
        'debug': True
    }

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

def settings_menu(config):
    while True:
        clear_console()
        print("=== Settings ===")
        print(f"1. studiomdl_path: {config['studiomdl_path']}")
        print(f"2. game_dir: {config['game_dir']}")
        print(f"3. Use -verbose: {'ON' if config['use_verbose'] else 'OFF'}")
        print(f"4. Use -nop4: {'ON' if config['use_nop4'] else 'OFF'}")
        print(f"5. Debug mode: {'ON' if config.get('debug') else 'OFF'}")

        choice = questionary.select(
            "Edit which setting?",
            choices=[
                "Change studiomdl_path",
                "Change game_dir",
                "Toggle -verbose",
                "Toggle -nop4",
                "Toggle debug mode",
                "Return"
            ]
        ).ask()

        if choice == "Change studiomdl_path":
            new_path = questionary.path("New studiomdl.exe path:").ask().strip()
            if os.path.isfile(new_path):
                config['studiomdl_path'] = new_path
                save_config(config)
            else:
                print("Invalid path. Press Enter to continue...")
                input()

        elif choice == "Change game_dir":
            new_dir = questionary.path("New game directory:").ask().strip()
            if os.path.isdir(new_dir):
                config['game_dir'] = new_dir
                save_config(config)
            else:
                print("Invalid directory. Press Enter to continue...")
                input()

        elif choice == "Toggle -verbose":
            config['use_verbose'] = not config['use_verbose']
            save_config(config)

        elif choice == "Toggle -nop4":
            config['use_nop4'] = not config['use_nop4']
            save_config(config)

        elif choice == "Toggle debug mode":
            config['debug'] = not config.get('debug', False)
            save_config(config)

        elif choice == "Return":
            clear_console()
            break

def debug_print(message, config):
    if config.get('debug'):
        print(f"[DEBUG] {message}")

def gather_files(root_dir, max_depth=2):
    """
    Recursively gather .smd and .dmx files up to max_depth in subfolders.
    Returns a dict with keys as immediate subfolder names and values as dict:
    {'smd': [...], 'dmx': [...]}
    """
    result = {}

    # List immediate subfolders in root_dir
    for subfolder in os.listdir(root_dir):
        subfolder_path = os.path.join(root_dir, subfolder)
        if not os.path.isdir(subfolder_path):
            continue

        smds = []
        dmxs = []

        # Walk with depth limit 2
        for current_path, dirs, files in os.walk(subfolder_path):
            # Calculate depth relative to subfolder_path
            rel_path = os.path.relpath(current_path, subfolder_path)
            depth = rel_path.count(os.sep)
            if depth > max_depth:
                # Don't go deeper
                dirs[:] = []
                continue

            for file in files:
                ext = file.lower().split('.')[-1]
                if ext == 'smd':
                    smds.append(os.path.join(current_path, file))
                elif ext == 'dmx':
                    dmxs.append(os.path.join(current_path, file))

        result[subfolder] = {'smd': smds, 'dmx': dmxs}

    return result

def make_qc_path(file_path, base_folder):
    return os.path.relpath(file_path, base_folder).replace("\\", "/")

def generate_qc():
    clear_console()
    
    root_dir = questionary.text("Enter Parent directory containing the content:").ask().strip()
    base_modelname = questionary.text("Enter base $modelname:").ask().strip()
    cdmaterials = questionary.text("Enter $cdmaterials:").ask().strip()

    files_by_folder = gather_files(root_dir, max_depth=2)

    for folder, file_dict in files_by_folder.items():
        smds = file_dict['smd']
        dmxs = file_dict['dmx']

        # Skip empty folders
        if not (smds or dmxs):
            continue

        folder_path = os.path.join(root_dir, folder)  # <--- moved here

        contains_nested = any(
            os.path.isdir(os.path.join(folder_path, subdir))
            for subdir in os.listdir(folder_path)
        )

        smds_with_triangles = []
        smds_without_triangles = []

        for smd_file in smds:
            try:
                with open(smd_file, 'r', encoding='utf-8', errors='ignore') as f:
                    contents = f.read()
                    if "triangles" in contents.lower():
                        smds_with_triangles.append(smd_file)
                    else:
                        smds_without_triangles.append(smd_file)
            except Exception as e:
                print(f"Could not read {smd_file}: {e}")

        # === Build QC content ===
        qc_lines = []

        # Only prefix folder name if it contains subfolders
        modelname = f"{base_modelname}/{folder}/{folder}.mdl" if contains_nested else base_modelname
        qc_lines.append(f"$modelname \"{modelname}\"")
        qc_lines.append(f'$cdmaterials "{cdmaterials}"\n')
        qc_lines.append('$maxverts 65530')

        for file_path in smds_with_triangles + dmxs:
            rel_path = make_qc_path(file_path, folder_path)

            qc_lines.append(f"$model \"{rel_path}\"")

        if smds_without_triangles:
            for smd_file in smds_without_triangles:
                rel_path = make_qc_path(smd_file, folder_path)
                sequence_name = os.path.splitext(os.path.basename(smd_file))[0]
                qc_lines.append(f"\n$sequence {sequence_name} {{")
                qc_lines.append(f"    \"{rel_path}\"")
                qc_lines.append("}")
        elif smds:
            rel_path = make_qc_path(smds[0], folder_path)
            qc_lines.append(f"\n$sequence idle {{")
            qc_lines.append(f"    \"{rel_path}\"")
            qc_lines.append("}")

        qc_lines.append("\n$mostlyopauqe")

        # === Write QC to subfolder ===
        folder_path = os.path.join(root_dir, folder)
        qc_filename = f"{folder}.qc" if contains_nested else "model.qc"
        qc_path = os.path.join(folder_path, qc_filename)

        try:
            with open(qc_path, 'w', encoding='utf-8') as f:
                f.write("\n".join(qc_lines))
            print(f"✓ Wrote QC to: {qc_path}")
        except Exception as e:
            print(f"Failed to write QC for {folder}: {e}")

compile_log = [] #stores studiomdl output

def compile_all_qc_files(studiomdl_path, game_dir, config):
    """Compiles all .qc files found recursively in the specified directory."""

    clear_console()

    global compile_log


    def showlog():
        while True:
            clear_console()

            if not compile_log:
                print("\n[~] No compiler output yet. Run 'Compile QCS' first.\n")
            else:
                print("\n[~] Compiler Log:\n" + "="*40)
                print("\n".join(compile_log))
                print("="*40 + "\n")

            action = questionary.select(
                "What do you want to do?",
                choices=[
                    "Return to Main Menu",
                    "Clear log",
                ]
            ).ask()

            if action == "Return to Main Menu":
                break
            elif action == "Clear log":
                compile_log.clear()
                print("\nLog cleared. Press Enter to continue...")
                input()

    def compile():
        clear_console()

        qc_parent_dir = questionary.text('Input the Parent QC folder:').ask().strip()

        def compile_qc_file(path):
            log_lines = [f"\n> Compiling: {path}", "=" * 40]

            process = subprocess.Popen(
                [studiomdl_path, "-game", game_dir, "-nop4", "-verbose", path],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )

            for line in process.stdout:
                stripped = line.strip()
                print(stripped)
                log_lines.append(stripped)

            process.wait()
            success = process.returncode == 0
            result = "v/ SUCCESS" if success else "/!\ FAILED"
            log_lines.append("=" * 40)
            log_lines.append(f"{result}: {path}\n")

            # Add this file's output to full compile log
            compile_log.extend(log_lines)
            return success

        # === Validate paths ===
        if not os.path.isfile(studiomdl_path):
            print("/!\ Error: studiomdl.exe not found.")
            return

        if not os.path.isdir(qc_parent_dir):
            print("/!\ Error: QC directory not found.")
            return

        # === Discover .qc files recursively ===
        qc_file_paths = [
            os.path.join(root, file)
            for root, _, files in os.walk(qc_parent_dir)
            for file in files if file.endswith('.qc')
        ]

        if not qc_file_paths:
            print("/!\ No .qc files found.")
            return

        print(f"Found {len(qc_file_paths)} .qc files. Starting compilation...\n")

        # === Compile all .qc files ===
        success_count = sum(compile_qc_file(path) for path in qc_file_paths)

        summary = f"\nv/ Compilation complete: {success_count}/{len(qc_file_paths)} succeeded.\n"
        print(summary)
        compile_log.append(summary)

    #menu logic 
    while True:    
        
        
        choice = questionary.select(
            "Choose an option:",
            choices=[
                "Compile QCS",
                "Show Log Of Compiler",
                "Options",
                "Return"
            ]
            ).ask()

        if choice == 'Compile QCS':
            compile()

        elif choice == 'Show Log Of Compiler':
            clear_console()
            showlog()

        elif choice == 'Options':
            settings_menu(config)
        
        elif choice == 'Return':
            clear_console()
            break
            

        else:
            print("/!\ Invalid choice")

def batch_generate_vmts():
    clear_console()
    
    def extract_materials_from_smds(directory):
        material_names = set()
        smd_files = glob.glob(os.path.join(directory, "**", "*.smd"), recursive=True)

        for smd_path in smd_files:
            with open(smd_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()

            in_triangles = False
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                if line == "triangles":
                    in_triangles = True
                    i += 1
                    continue
                if in_triangles:
                    if line == "end":
                        break
                    if re.match(r'^[A-Za-z0-9_\-\.]+$', line):
                        material_names.add(line)
                        i += 4
                    else:
                        i += 1
                else:
                    i += 1
        return sorted(material_names)

    def extract_cdmaterials_paths(qc_path):
        cdmaterials = set()
        with open(qc_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                match = re.search(r'\$cdmaterials\s+"([^"]+)"', line, re.IGNORECASE)
                if match:
                    cdmaterials.add(match.group(1).strip().replace('\\', '/').rstrip('/'))
        return list(cdmaterials)

    def find_best_vtfs_for_material(material_names, vtf_dir, color_suffixes, normal_suffixes):
        vtf_files = [os.path.basename(vtf).lower().replace('.vtf', '') for vtf in glob.glob(os.path.join(vtf_dir, "*.vtf"))]
        matched_textures = {}

        for mat in material_names:
            mat_lower = mat.lower()
            best_color = None
            best_normal = None
            best_color_score = 0
            best_normal_score = 0

            for vtf in vtf_files:
                score = fuzz.partial_ratio(mat_lower, vtf)
                if any(vtf.endswith(suffix.lower()) for suffix in color_suffixes) and score > best_color_score:
                    best_color = vtf
                    best_color_score = score
                elif any(vtf.endswith(suffix.lower()) for suffix in normal_suffixes) and score > best_normal_score:
                    best_normal = vtf
                    best_normal_score = score

            matched_textures[mat] = {
                'color': best_color,
                'normal': best_normal
            }

        return matched_textures

    def save_as_vmt(material_names, output_base_dir, texture_paths=None, default_template=''):
        for name in material_names:
            content = default_template
            if texture_paths and name in texture_paths:
                tex = texture_paths[name]
                base = f'"$basetexture" "models/{tex["color"]}"' if tex.get("color") else ''
                bump = f'"$bumpmap" "models/{tex["normal"]}"' if tex.get("normal") else ''
                content = content.replace('"$basetexture" ""', base or '"$basetexture" ""')
                content = content.replace('"$bumpmap"     ""', bump or '"$bumpmap"     ""')

            output_dir = os.path.join(output_base_dir)
            os.makedirs(output_dir, exist_ok=True)
            vmt_path = os.path.join(output_dir, f"{name}.vmt")
            with open(vmt_path, 'w', encoding='utf-8') as vmt_file:
                vmt_file.write(content)

    def find_model_subfolders(parent_dir):
        debug_print(f"Scanning for model subfolders in: {parent_dir}", config)
        valid_subfolders = set()
        for root, dirs, files in os.walk(parent_dir):
            has_smd = any(f.lower().endswith(".smd") for f in files)
            has_qc = any(f.lower().endswith(".qc") for f in files)
            if has_smd or has_qc:
                debug_print(f"Found valid model folder: {root}", config)
                valid_subfolders.add(root)
        return sorted(valid_subfolders)

    # ------------------- User Inputs -------------------
    while True:
        parent_directory = questionary.path("Enter path to parent model directory: ").ask().strip()
        config = load_config()  # Load early to use for debug printing
        debug_print(f"User provided directory: {parent_directory}", config)
        model_dirs = find_model_subfolders(parent_directory)
        if model_dirs:
            debug_print(f"Found {len(model_dirs)} valid model folder(s).", config)
            break
        else:
            print("/!\\ No .smd or .qc files found in any subdirectories. Try again.")

    game_materials_dir = os.path.join(config['game_dir'], 'materials')
    debug_print(f"Game materials directory: {game_materials_dir}", config)

    for model_dir in model_dirs:
        print(f"\n--- Processing: {model_dir} ---")

        smd_files = glob.glob(os.path.join(model_dir, "*.smd"))
        qc_files = glob.glob(os.path.join(model_dir, "*.qc"))
        debug_print(f"Found {len(smd_files)} SMDs, {len(qc_files)} QCs.", config)

        if not smd_files:
            print("  Skipped — no .smd files found.")
            continue

        # Extract materials
        materials = extract_materials_from_smds(model_dir)
        debug_print(f"Extracted {len(materials)} materials from SMDs.", config)

        if not materials:
            print("  No materials found in .smds.")
            continue

        # Extract $cdmaterials
        cdmaterials_paths = set()
        for qc in qc_files:
            paths = extract_cdmaterials_paths(qc)
            cdmaterials_paths.update(paths)
            debug_print(f"Extracted $cdmaterials from {qc}: {paths}", config)

        print(f"  Found materials:")
        for mat in materials:
            print(f"    - {mat}")

        if cdmaterials_paths:
            print(f"  Found $cdmaterials paths:")
            for p in cdmaterials_paths:
                print(f"    - {p}")
        else:
            print("  No $cdmaterials paths found.")

        default_cdmat = list(cdmaterials_paths)[0] if cdmaterials_paths else "models"
        output_base_dir = os.path.join(game_materials_dir, default_cdmat)
        debug_print(f"VMTs will be saved to: {output_base_dir}", config)

        while True:
            answer = questionary.text("Use $cdmaterials as VTF texture folder? (y/n): ").ask()
            if answer is None:
                continue  # handle empty input or Ctrl+C gracefully if needed
            answer = answer.strip().lower()
            if answer in ('y', 'n'):
                use_cdmat_for_vtf = (answer == 'y')
                break
            print("Please enter 'y' or 'n' and then press Enter.")

        debug_print(f"Use cdmaterials for VTF input: {use_cdmat_for_vtf}", config)

        if use_cdmat_for_vtf and cdmaterials_paths:
            vtf_dirs = [
                os.path.join(
                    game_materials_dir,
                    path.replace("\\", "/").lstrip("/").removeprefix("materials/")
                ) for path in cdmaterials_paths
            ]
            vtf_files = []
            for d in vtf_dirs:
                found = glob.glob(os.path.join(d, "*.vtf"))
                vtf_files += found
                debug_print(f"Found {len(found)} VTFs in: {d}", config)

            if not vtf_files:
                print("  No .vtf files found in $cdmaterials folders. Falling back to manual input.")
                use_cdmat_for_vtf = False

        if not use_cdmat_for_vtf:
            while True:
                vtf_dir = questionary.path("Enter path to VTF directory: ").ask().strip()
                debug_print(f"User VTF directory input: {vtf_dir}", config)
                vtf_files = glob.glob(os.path.join(vtf_dir, "*.vtf"))
                debug_print(f"Found {len(vtf_files)} VTFs.", config)
                if vtf_files:
                    break
                else:
                    print("/!\\ Directory doesn't contain any .vtf files. Please try again.")

        vmtTemplate = '''"VertexLitGeneric"
    {
        "$basetexture" ""
        "$bumpmap"     ""

        "$phong" "1"
        "$phongboost" "1"
        "$phongexponent" "1"

    //generated by LambdaConstruct
    }
    '''

        enable_fuzzy = questionary.text("\nEnable fuzzy texture matching? (y/n): ").ask().strip().lower() == 'y'
        debug_print(f"Fuzzy texture matching: {enable_fuzzy}", config)

        if enable_fuzzy:
            color_suffixes = input("Enter color texture suffix(es), comma-separated (e.g. col,diff): ").split(',')
            normal_suffixes = input("Enter normal texture suffix(es), comma-separated (e.g. nrm,norm): ").split(',')
            debug_print(f"Color suffixes: {color_suffixes}", config)
            debug_print(f"Normal suffixes: {normal_suffixes}", config)

            if use_cdmat_for_vtf:
                debug_print("Creating temp dir for VTF matching from cdmaterials folders.", config)
                temp_vtf_dir = os.path.join(model_dir, "_combined_vtf_temp")
                os.makedirs(temp_vtf_dir, exist_ok=True)
                for file in vtf_files:
                    dst = os.path.join(temp_vtf_dir, os.path.basename(file))
                    if not os.path.exists(dst):
                        try:
                            os.link(file, dst)
                            debug_print(f"Linked VTF: {file} -> {dst}", config)
                        except:
                            shutil.copy2(file, dst)
                            debug_print(f"Copied VTF: {file} -> {dst}", config)
                texture_paths = find_best_vtfs_for_material(materials, temp_vtf_dir, color_suffixes, normal_suffixes)
            else:
                texture_paths = find_best_vtfs_for_material(materials, vtf_dir, color_suffixes, normal_suffixes)

            debug_print("Matched textures:", config)
            for mat, tex in texture_paths.items():
                debug_print(f"{mat} -> color: {tex['color']} | normal: {tex['normal']}", config)

            save_as_vmt(materials, output_base_dir, texture_paths, default_template=vmtTemplate)
        else:
            debug_print("Saving VMTs with template only (no textures).", config)
            save_as_vmt(materials, output_base_dir, texture_paths=None, default_template=vmtTemplate)

def setup():
    clear_console()
    print("=== Initial Setup ===\n")

    while True:
        studiomdl_path = questionary.path("Enter full path to studiomdl.exe:").ask().strip()
        if os.path.isfile(studiomdl_path):
            break
        else:
            print("Invalid file path. Press Enter to try again...")
            input()

    while True:
        game_dir = questionary.path("Enter full path to game directory:").ask().strip()
        if os.path.isdir(game_dir):
            break
        else:
            print("Invalid directory path. Press Enter to try again...")
            input()

    config = {
        'studiomdl_path': os.path.abspath(studiomdl_path),
        'game_dir': os.path.abspath(game_dir),
        'use_verbose': True,
        'use_nop4': True,
        'debug' : False
    }

    save_config(config)
    print("\nSetup complete. Press Enter to continue...")
    input()
    return config

def main_menu():
    result = button_dialog(
        title='LambdaConstruct',
        text='Welcome to LambdaConstruct\nChoose a Tab:',
        buttons=[
            ('Make QCs', 'qc'),
            ('Compile QCs', 'compile'),
            ('Make VMTs', 'vmt'),
            ('Settings', 'settings'),
            ('Exit', 'exit')
        ],
        style=dark_mode_style
    ).run()

    return result

def main():
    config = load_config()

    if not os.path.exists(CONFIG_FILE):
        config = setup()
    else:
        config = load_config()

    while True:
        usr = main_menu()

        if usr == 'qc':
            generate_qc()

        elif usr == 'compile':

            print('In Compile Tab\n')

            compile_all_qc_files(
                studiomdl_path=config['studiomdl_path'],
                game_dir=config['game_dir'],
                config=config
            )

        elif usr == 'vmt':
            batch_generate_vmts()

        elif usr == 'settings':
            settings_menu(config)

        elif usr == 'exit':
            clear_console()
            break

if __name__ == "__main__":
    main()
