from src.lib.SMDpraser import SMDFile

smd = SMDFile(r"D:\models\scp\weapons\Revolver\44_revolver.smd")

# Print materials
for mat in smd.materials:
    print(mat)