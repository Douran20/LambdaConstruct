# LambdaConstruct
LambdaConstruct is a Source Engine Batch Model Porting Utility design to speed up the process
---

## about

LambdaConstruct is designed to **streamline and automate the workflow** for batch creating and compiling models 
for those Source Engine porters. It eliminates the repetitive process of making QCs and VMTs for every model

---

## usage

**Lambda Construct** is used to Generate QCS and VMTS and Batch compile MDL's

### How it Works


### Generate QC tab
u first input wiil be your parent directory that contains all of your models - *Note: as of now we only support SMD files. dmx implentation is currently being thought of*
```
parent/
├── models/
│   │ ├── model.qc
│   │ ├── model1.smd
│   │ ├── model2.smd
```

```bash
? Input Parent Dir: Example\Path
```
after so u input a $modelname 

### How to Launch the LambdaConstruct.py

- install python 3.11 or higher
- install prompt_toolkit and questionary
```bash
pip install prompt_toolkit questionary
```
Launch the python file
```bash
python LambdaConstruct.py

