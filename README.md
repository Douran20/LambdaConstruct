# LambdaConstruct
LambdaConstruct is a Source Engine Batch Model Porting Utility for Windows
---

## about

LambdaConstruct is designed to **streamline and automate the workflow** for batch creating and compiling models 
for those Source Engine porters. It eliminates the repetitive process of making QCs and VMTs for every model

---

## usage

**Lambda Construct** is used to Generate QCS and VMTS and Batch compile MDL's

### Make QC tab
u first input wiil be your parent directory that contains all of your models - *Note: as of now we only support SMD files. dmx implentation is currently being thought of*
```
parent/
├── Character01/
│   │ ├── model1.smd
│   │ ├── model2.smd
```

```
? Enter Parent directory containing the content: C:\parent
```
this will make a qc for every sub-directory that contains smds in your parent-directory

after so u input a $modelname. this will be used in the $modelname - *Note: the subfolder will be added as the mdl and as a folder before it*

```
? Enter base $modelname: Douran\Fortnite\Characters
```
result in qc
```
$modelname "Douran\Fortnite\Characters\Character01\Character01.mdl"
```
last step in the process is to input your $cdmaterials
```
? Enter $cdmaterials: models\Douran\Fortnite\Characters\01
```
result in qc
```
$cdmaterials "models\Douran\Fortnite\Characters\01"
```

after u hit enter it will start generating qcs

---

### Compile QC tab

U have 3 Options to pick from
```
? Choose an option: (Use arrow keys)
   Compile QCS
   Show Log Of Compiler
   Options
   Return
```

#### Compile QCS

u will need to input the parentfolder that contain all of your qcs.
(it will search for .qc files recursively)
```
? Input the Parent QC folder: C:\QC_folder
```

after so it will start ```studiomdl.exe``` and compile all of the qcs files found one by one. u can see the output as it goes. - *Note : u can scroll up to see the output of ```studiomdl.exe```*

#### Show Log Of Compiler
its in the name.
u can scroll up and down to view it
u can clear it as well
this log will get erased after u close the exe

---

#### Options

the samething as settings

---

### Settings tab

u can change the studiomdl.exe directory

u can change the gameinfo directory - *Note : its the folder that contains your gameinfo.txt*

Turn On/Off ```-verbose``` : Show detailed compiler output.

Turn On/Off ```-nop4``` : Skip Perforce-related operations.

---

### Make VMTs
This generates .vmt material files from materials referenced in .smd model files.

Folder containing .smd files so it can generating vmts
```
Enter path to model directory: 
```
Export Directory for the Vmts
```
? Enter path to output .vmt directory: 
```
input y for yes input n for no
```
Enable fuzzy texture matching? (y/n): 
```
if Y its Enable automatic matching between material names and textures.

example :
```
│   │ ├── RavenTeamLeader.vmt
│   │ ├── RavenTeamLeader_Texture.vtf

if the names roughly match RavenTeamLeader_Texture.vtf will be added into RavenTeamLeader.vmt

Output : $basetexture "RavenTeamLeader_Texture.vtf"
```

if n it will just output a basic vmt for u to edit later
```
```

---

### How to Launch the LambdaConstruct.py

- install [python](https://www.python.org/) 3.11 or higher
- install prompt_toolkit, questionary and rapidfuzz

```bash
pip install prompt_toolkit questionary rapidfuzz
```
Launch the python file
```bash
python LambdaConstruct.py
```

## Issues

### anims

currently the logic for adding smds into the qc is very basic. if it sees a smd it just adds it as a $Model line. and having subfolders will also generating qcs. i do plan on added better logic for this later
