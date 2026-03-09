Set WshShell = CreateObject("WScript.Shell")
' Ejecuta el archivo start.bat en modo oculto (0)
WshShell.Run "cmd /c start.bat", 0, False
