SET F=".\dist"
IF EXIST %F% RMDIR /S /Q %F%

pyinstaller --clean --onefile --specpath .\build --name "Hornydivers" --noconsole hornydivers.py 
pyinstaller --clean --onefile --specpath .\build --name "Hornydivers (With Console)" hornydivers.py
xcopy .\templates .\dist\templates\

RMDIR /S /Q ".\build"
PAUSE