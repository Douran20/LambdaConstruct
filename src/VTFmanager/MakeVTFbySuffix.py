import os
import json
import subprocess
import argparse
import re

# --------------------------------------------------------------------
# Constants and Defaults
# --------------------------------------------------------------------

CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'config', 'vtf_suffix.json')
DEFAULT_VTFCMD = os.path.join(os.path.dirname(__file__), 'VTFCmd')

DEFAULT_CONFIG = {
    "vtfcmd_path": "{DEFAULT_VTFCMD}VTFCmd.exe",
    "rules": {
        "_normal": {"format": "RGBA8888", "alphaformat": "RGBA8888", "extra_flags": ["-nomipmaps"]},
        "_alpha":  {"format": "DXT5",     "alphaformat": "DXT5",     "extra_flags": ["-nomipmaps"]},
        "_color":  {"format": "DXT1",     "alphaformat": None,       "extra_flags": ["-nomipmaps"]},
        "default": {"format": "DXT1",     "alphaformat": None,       "extra_flags": ["-nomipmaps"]}
    }
}

SUPPORTED_EXTENSIONS = ['.tga', '.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff', '.dds']

# --------------------------------------------------------------------
# Configuration Management
# --------------------------------------------------------------------

def load_config():
    if not os.path.exists(CONFIG_FILE):
        config = json.loads(json.dumps(DEFAULT_CONFIG))
        config["vtfcmd_path"] = config["vtfcmd_path"].replace(
            "{DEFAULT_VTFCMD}", DEFAULT_VTFCMD + os.sep
        )
        save_config(config)
        return config

    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)
    print(f"Config saved to {CONFIG_FILE}.")

def print_rules(rules):
    print("\nCurrent suffix rules:")
    for suffix, rule in rules.items():
        print(f"  {suffix}:")
        print(f"    format: {rule.get('format')}")
        print(f"    alphaformat: {rule.get('alphaformat')}")
        print(f"    extra_flags: {', '.join(rule.get('extra_flags', []))}")
    print()

# --------------------------------------------------------------------
# User Input Helpers
# --------------------------------------------------------------------

def prompt_input(prompt, default=None, allow_empty=True):
    prompt = f"{prompt} [default: {default}]: " if default is not None else f"{prompt}: "
    while True:
        val = input(prompt).strip()
        if val == '' and default is not None:
            return default
        if val == '' and not allow_empty:
            print("Input cannot be empty.")
            continue
        return val

def prompt_list(prompt, default=None):
    val = prompt_input(prompt, default)
    return [x.strip() for x in val.split(',') if x.strip()] if val else []

# --------------------------------------------------------------------
# Configuration Manager Menu
# --------------------------------------------------------------------

def config_manager():
    config = load_config()
    while True:
        print("\n[ VTF Config Manager ]")
        print("1. View current suffix rules")
        print("2. Add new suffix rule")
        print("3. Edit existing suffix rule")
        print("4. Remove suffix rule")
        print("5. Set VTFCmd path")
        print("6. Reset to defaults")
        print("7. Exit")

        choice = input("Choose an option (1-7): ").strip()

        if choice == '1':
            print_rules(config['rules'])

        elif choice == '2':
            suffix = prompt_input("Enter suffix (e.g. _exponent)", allow_empty=False).lower()
            if suffix in config['rules']:
                print(f"Suffix '{suffix}' already exists. Use Edit to modify.")
                continue
            fmt = prompt_input("Enter format", default="DXT1")
            alpha = prompt_input("Enter alpha format (or 'none')", default="none")
            alpha = None if alpha.lower() == 'none' else alpha
            flags = prompt_list("Enter extra flags (comma-separated)", default="-nomipmaps")
            config['rules'][suffix] = {"format": fmt, "alphaformat": alpha, "extra_flags": flags}
            print(f"Added rule for suffix '{suffix}'.")
            save_config(config)

        elif choice == '3':
            suffix = prompt_input("Enter suffix to edit", allow_empty=False).lower()
            if suffix not in config['rules']:
                print(f"No rule found for suffix '{suffix}'.")
                continue
            rule = config['rules'][suffix]
            fmt = prompt_input("Enter format", default=rule.get('format'))
            alpha = prompt_input("Enter alpha format (or 'none')", default=rule.get('alphaformat') or 'none')
            alpha = None if alpha.lower() == 'none' else alpha
            flags = prompt_list("Enter extra flags (comma-separated)", default=",".join(rule.get('extra_flags', [])))
            config['rules'][suffix] = {"format": fmt, "alphaformat": alpha, "extra_flags": flags}
            print(f"Updated rule for suffix '{suffix}'.")
            save_config(config)

        elif choice == '4':
            suffix = prompt_input("Enter suffix to remove", allow_empty=False).lower()
            if suffix not in config['rules']:
                print(f"No rule found for suffix '{suffix}'.")
                continue
            if input(f"Are you sure you want to remove '{suffix}'? (y/n): ").lower() == 'y':
                del config['rules'][suffix]
                print(f"Removed rule for suffix '{suffix}'.")
                save_config(config)

        elif choice == '5':
            current_path = config.get('vtfcmd_path', 'VTFCmd.exe')
            print(f"Current VTFCmd path: {current_path}")
            new_path = prompt_input("Enter new VTFCmd path", default=current_path)
            if not os.path.exists(new_path):
                print("Warning: The specified path does not exist.")
            config['vtfcmd_path'] = new_path
            print(f"VTFCmd path updated to: {new_path}")
            save_config(config)

        elif choice == '6':
            if input("Reset all settings to defaults? This cannot be undone. (y/n): ").lower() == 'y':
                config = json.loads(json.dumps(DEFAULT_CONFIG))
                config["vtfcmd_path"] = config["vtfcmd_path"].replace(
                    "{DEFAULT_VTFCMD}", DEFAULT_VTFCMD + os.sep
                )
                save_config(config)
                print("Settings reset to defaults.")

        elif choice == '7':
            break

        else:
            print("Invalid choice, please enter a number 1-7.")

# --------------------------------------------------------------------
# Conversion Logic
# --------------------------------------------------------------------

def get_rule_for_file(rules, filename):
    filename = filename.lower()
    for suffix, rule in rules.items():
        if suffix != "default" and filename.endswith(suffix):
            return rule
    return rules.get("default")

def run_vtfcmd(file_path, output_path, vtfcmd_path, rule):
    if not os.path.exists(file_path):
        print(f"[X] Input file not found: {file_path}")
        return False

    os.makedirs(output_path, exist_ok=True)

    cmd = [
        vtfcmd_path,
        '-file', file_path,
        '-format', rule['format'],
        '-output', output_path
    ]

    if rule.get('alphaformat'):
        cmd += ['-alphaformat', rule['alphaformat']]
    if rule.get('extra_flags'):
        cmd += rule['extra_flags']

    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"[✓] Converted: {file_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[X] Failed: {file_path}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False

def batch_convert_folder(input_folder, output_folder, vtfcmd_path, rules):
    if not os.path.exists(input_folder):
        print(f"Input folder not found: {input_folder}")
        return

    for file in os.listdir(input_folder):
        if any(file.lower().endswith(ext) for ext in SUPPORTED_EXTENSIONS):
            file_path = os.path.join(input_folder, file)
            rule = get_rule_for_file(rules, file)
            run_vtfcmd(file_path, output_folder, vtfcmd_path, rule)

# --------------------------------------------------------------------
# Input/Output List Parser
# --------------------------------------------------------------------

def parse_io_line(line):
    input_match = re.search(r'input\s*=\s*"([^"]+)"', line)
    output_match = re.search(r'output\s*=\s*"([^"]+)"', line)
    if not input_match:
        raise ValueError(f"Line missing input: {line}")
    return input_match.group(1), output_match.group(1) if output_match else input_match.group(1)

def read_io_list(file_path):
    pairs = []
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            try:
                pairs.append(parse_io_line(line))
            except ValueError as e:
                print(f"Skipping line: {e}")
    return pairs

# --------------------------------------------------------------------
# Main CLI Handler
# --------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Batch convert textures to VTF format using VTFCmd.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('-input', '-i', help="Input folder containing image files.")
    parser.add_argument('-output', '-o', help="Output folder for VTF files.")
    parser.add_argument('-vtfcmd', '-v', help="Path to VTFCmd.exe (overrides config).")
    parser.add_argument('--config', '-c', action='store_true', help="Open config manager.")
    parser.add_argument('-list', '-l', help='Text file with input/output folders: input="..." output="..."')

    args = parser.parse_args()
    config = load_config()

    if args.config:
        config_manager()
        return

    vtfcmd_path = args.vtfcmd or config['vtfcmd_path']

    if args.list:
        for input_folder, output_folder in read_io_list(args.list):
            print(f"\nProcessing input: {input_folder}")
            print(f"Output folder: {output_folder}")
            batch_convert_folder(input_folder, output_folder, vtfcmd_path, config['rules'])

    elif args.input:
        output_folder = args.output or args.input
        batch_convert_folder(args.input, output_folder, vtfcmd_path, config['rules'])

    else:
        print("No input folder specified. Use --input/-i or --list/-l.")
        parser.print_help()

# --------------------------------------------------------------------
# call
# --------------------------------------------------------------------

if __name__ == '__main__':
    main()
