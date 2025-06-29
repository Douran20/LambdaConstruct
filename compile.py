import PyInstaller.__main__

PyInstaller.__main__.run([
    'batchporter.py',
    '--name=LambdaConstruct',
    '--onefile',
    '--icon=icon.ico'
])