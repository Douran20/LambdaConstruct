# LambdaConstruct
LambdaConstruct is a Source Engine Batch Model Porting Utility for Windows
---

## about

LambdaConstruct **streamline and automate the workflow** for batch creating and compiling models 
for those Source Engine porters. It eliminates the repetitive process of making QCs, Compiling, and VMTs for every model

---

## usage

**Lambda Construct** are python scripts that u execute in a command line with the python interperter.

ie:
```bash
python compileQCs.py  
```
if your not tech "savvy" u need to install the python lang.
u can just get it from they're [site](https://www.python.org/).


### install

- install [python](https://www.python.org/) 3.11 or higher
- install the [release](https://github.com/Douran20/LambdaConstruct)

---
### compileQCs.py
```text
options:
   -h, --help            show this help message and exit
   -compile COMPILE      Path to compile.txt config file
   -qc QC                Path to .qc file(s). Can be used multiple times.
   -game GAME            Path to game folder (must contain gameinfo.txt)
   -studiomdl STUDIOMDL  Path to studiomdl.exe
   -logdir LOGDIR        Folder to write log files to (default: logs/)
   -nolog                Disable log file output
   -qcfolder QCFOLDER    Folder path to scan recursively for .qc files to batch compile
   -clearlogs            Delete all files in the log folder before compiling
```

#### -compile 
`-compile` is a list file input. it contains the -qc inputs as qc, -game as game, and lastly -studiomdl as studiomdl.

example.txt
```text
qc="D:\qc\example.qc"
qcfolder="D:\qc"
game="D:\SteamLibrary\steamapps\common\SourceFilmmaker\game\usermod"
studiomdl="D:\SteamLibrary\steamapps\common\SourceFilmmaker\game\bin\studiomdl.exe"
```

u can override game and studiomdl with their repective args in the command line

ie:
```bash
python compileQCs.py -compile list.txt -studiomdl "E:\csgo\studiomdl.exe" -game "D:\SteamLibrary\steamapps\common\Bobs Filmmaker\game\usermod"
```

u can also append -qc inputs in the command line

ie:
```bash
python compileQCs.py -compile list.txt -qc "D:\qcs2"
```

---

### file_orgainztion.py
nothing for now

---

## Issues
none lol
