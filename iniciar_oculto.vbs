' Inicia o alarme em background, sem janela de console (pythonw = sem console)
Set WshShell = CreateObject("WScript.Shell")
scriptDir = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = scriptDir
WshShell.Run "pythonw.exe """ & scriptDir & "\alarme.py""", 0, False
Set WshShell = Nothing
