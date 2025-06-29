import json

import glob
import os
import subprocess

import re
from rapidfuzz import fuzz

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
    # Default configuration
    return {
        'studiomdl_path': '',
        'game_dir': '',
        'use_verbose': True,
        'use_nop4': True
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

        choice = questionary.select(
            "Edit which setting?",
            choices=[
                "Change studiomdl_path",
                "Change game_dir",
                "Toggle -verbose",
                "Toggle -nop4",
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

        elif choice == "Return":
            clear_console()
            break

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
    
    root_dir = questionary.text("Enter directory containing dmxs and smds:").ask().strip()
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

    def generate_vmt_content(texture_paths):
        lines = ['"VertexLitGeneric"\n{']
        if texture_paths.get('color'):
            lines.append(f'    "$basetexture" "models/{texture_paths["color"]}"')
        if texture_paths.get('normal'):
            lines.append(f'    "$bumpmap" "models/{texture_paths["normal"]}"')
        lines.append('}')
        return "\n".join(lines)

    def save_as_vmt(material_names, output_dir, texture_paths=None, default_template=''):
        os.makedirs(output_dir, exist_ok=True)

        for name in material_names:
            vmt_path = os.path.join(output_dir, f"{name}.vmt")
            with open(vmt_path, 'w', encoding='utf-8') as vmt_file:
                if texture_paths:
                    content = generate_vmt_content(texture_paths.get(name, {}))
                else:
                    content = default_template
                vmt_file.write(content)

    while True:
        directory = questionary.path("Enter path to model directory: ").ask().strip()
        smd_files = glob.glob(os.path.join(directory, "*.smd"))
        if smd_files:
            break
        else:
            print("/!\ Directory doesn't contain any .smd files. Please try again.")

    output_vmt_dir = questionary.path("Enter path to output .vmt directory: ").ask().strip()
    while True:
        vtf_dir = questionary.path("Enter path to VTF directory (usually same as vmt dir): ").ask().strip()
        vtf_files = glob.glob(os.path.join(vtf_dir, "*.vtf"))
        if vtf_files:
            break
        else:
            print("/!\ Directory doesn't contain any .vtf files. Please try again.")

    materials = extract_materials_from_smds(directory)
    print("\nFound material names:")
    for mat in materials:
        print(f"  - {mat}")

    enable_fuzzy = input("\nEnable fuzzy texture matching? (y/n): ").strip().lower() == 'y'

    if enable_fuzzy:
        color_suffixes = input("Enter color texture suffix(es), comma-separated (e.g. col,diff): ").split(',')
        normal_suffixes = input("Enter normal texture suffix(es), comma-separated (e.g. nrm,norm): ").split(',')
        texture_paths = find_best_vtfs_for_material(materials, vtf_dir, color_suffixes, normal_suffixes)
        save_as_vmt(materials, output_vmt_dir, texture_paths)
    else:
        vmtTemplate = '''"VertexLitGeneric"
{
    "$basetexture" "models/your_texture_here"
}
'''
        save_as_vmt(materials, output_vmt_dir, texture_paths=None, default_template=vmtTemplate)

    print(f"\n✔ Saved {len(materials)} .vmt files to '{output_vmt_dir}'")

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
        'use_verbose': False,
        'use_nop4': False
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
