import subprocess
import os
import sys
import argparse
import time

def parse_compilefile(path):

    config = {
        "qc": [],
        "game": None,
        "studiomdl": None,
        "qcfolder": None
    }

    with open(path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip().lower()
                value = value.strip().strip('"').strip("'")

                if key == 'qc':
                    config["qc"].append(value)
                elif key in config:
                    config[key] = value
                elif key == "qcfolder":
                    config["qcfolder"] = value

    return config

def run_studiomdl(studiomdl, game, qc_file, log_dir, enable_logging=True):
    if not os.path.isfile(studiomdl):
        raise FileNotFoundError(f"studiomdl.exe not found at: {studiomdl}")
    if not os.path.isdir(game):
        raise FileNotFoundError(f"Game path not found: {game}")
    if not os.path.isfile(qc_file):
        raise FileNotFoundError(f"QC file not found: {qc_file}")

    command = [
        studiomdl,
        "-game", game,
        "-nop4",
        "-verbose",
        qc_file
    ]

    qc_name = os.path.splitext(os.path.basename(qc_file))[0]
    log_file_path = os.path.join(log_dir, f"{qc_name}_compile.log") if enable_logging else None

    print(f"\nCompiling: {qc_file}")
    if enable_logging:
        print(f"Logging to: {log_file_path}\n")
    else:
        print("Logging disabled\n")

    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

    log_file = open(log_file_path, 'w', encoding='utf-8') if enable_logging else None

    for line in process.stdout:
        print(line, end='')
        if log_file:
            log_file.write(line)

    process.wait()

    if log_file:
        log_file.close()

    if process.returncode == 0:
        print(f"\nCompile succeeded: {qc_file}\n")
    else:
        print(f"\nCompile failed: {qc_file} (exit code {process.returncode})\n")
def main():
    parser = argparse.ArgumentParser(description="Compile Source Engine .qc files using studiomdl.exe")
    parser.add_argument("-compile", help="Path to compile.txt config file")
    parser.add_argument("-qc", action='append', help="Path to .qc file(s). Can be used multiple times.")
    parser.add_argument("-game", help="Path to game folder (must contain gameinfo.txt)")
    parser.add_argument("-studiomdl", help="Path to studiomdl.exe")
    parser.add_argument("-logdir", default="logs", help="Folder to write log files to (default: logs/)")
    parser.add_argument("-nolog", action="store_true", help="Disable log file output")
    parser.add_argument("-qcfolder", help="Folder path to scan recursively for .qc files to batch compile")
    parser.add_argument("-clearlogs", action="store_true", help="Delete all files in the log folder before compiling")

    args = parser.parse_args()

    config = {
        "qc": [],
        "game": None,
        "studiomdl": None
    }

    if args.compile:
        if not os.path.isfile(args.compile):
            print(f"Compile file not found: {args.compile}")
            sys.exit(1)
        file_config = parse_compilefile(args.compile)
        config.update({k: v for k, v in file_config.items() if v})

    qc_files_from_folder = []
    folder_to_scan = args.qcfolder or config.get("qcfolder")

    if folder_to_scan:
        if not os.path.isdir(folder_to_scan):
            print(f"QC folder not found: {folder_to_scan}")
            sys.exit(1)
        for root, dirs, files in os.walk(folder_to_scan):
            for file in files:
                if file.lower().endswith('.qc'):
                    qc_files_from_folder.append(os.path.join(root, file))

        if not qc_files_from_folder:
            print(f"No QC files found in folder: {folder_to_scan}")
            sys.exit(1)

    if args.qc:
        config["qc"] = args.qc
    elif qc_files_from_folder:
        config["qc"] = qc_files_from_folder

    if args.game:
        config["game"] = args.game
    if args.studiomdl:
        config["studiomdl"] = args.studiomdl

    if not config["qc"]:
        print("No QC files specified.")
        sys.exit(1)
    if not config["game"] or not config["studiomdl"]:
        print("Missing required paths: game folder and/or studiomdl.exe.")
        sys.exit(1)

    if not args.nolog:
        os.makedirs(args.logdir, exist_ok=True)

        if args.clearlogs:
            print(f"Clearing log directory: {args.logdir}")
            for filename in os.listdir(args.logdir):
                file_path = os.path.join(args.logdir, filename)
                if os.path.isfile(file_path):
                    try:
                        os.remove(file_path)
                    except Exception as e:
                        print(f"Failed to delete {file_path}: {e}")

    total_start = time.time()

    for qc_path in config["qc"]:
        try:
            print(f"Starting compile: {qc_path}")
            start = time.time()

            run_studiomdl(config["studiomdl"], config["game"], qc_path, args.logdir, enable_logging=not args.nolog)

            end = time.time()
            elapsed = end - start
            print(f"Compile time for '{qc_path}': {elapsed:.2f} seconds\n")
        except FileNotFoundError as e:
            print(e)

    total_end = time.time()
    total_elapsed = total_end - total_start
    print(f"Total compile time: {total_elapsed:.2f} seconds")

if __name__ == "__main__":
    main()
