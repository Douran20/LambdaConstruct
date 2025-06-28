# LambdaConstruct
LambdaConstruct is a Source Engine Batch Model Porting Utility design to speed up the process
![logo.png]
---

## about

LambdaConstruct is designed to **streamline and automate the workflow** for batch creating and compiling models 
for those Source Engine porters. It eliminates the repetitive process of making QCs and VMTs for every model

---

## usage

**Lambda Construct** is used to Generate QCS and VMTS and Batch compile MDL's

### Generate QC tab
u first input wiil be your parent directory that contains all of your models - *Note: as of now we only support SMD files. dmx implentation is currently being thought of*
```
parent/
├── Character01/
│   │ ├── model1.smd
│   │ ├── model2.smd
```

```
? Input Parent Dir: C:\parent
```
this will make a qc for every sub-directory that contains smds in your parent-directory

after so u input a $modelname. this will be used in the $modelname - *Note: the subfolder will be added as the mdl and as a folder before it*

```
? Input $modelname Dir: Douran\Fortnite\Characters
```
result in qc
```
$modelname "Douran\Fortnite\Characters\Character01\Character01.mdl"
```
last step in the process is to input your $cdmaterials
```
Input $cdmaterials Dir: models\Douran\Fortnite\Characters\01
```
result in qc
```
$cdmaterials "models\Douran\Fortnite\Characters\01"
```

after u hit enter it will start generating qcs

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



### How to Launch the LambdaConstruct.py - OPTIONAL

- install [python](https://www.python.org/) 3.11 or higher
- install prompt_toolkit and questionary

Windows
```bash
pip install prompt_toolkit questionary
```
Launch the python file
```bash
python LambdaConstruct.py
```
