Set WshShell = CreateObject("WScript.Shell")
strDesktop = WshShell.SpecialFolders("Desktop")
strPath = WshShell.CurrentDirectory

' 1. Crear el acceso directo en el escritorio (Solo si no existe o para actualizar ruta)
Set oShortCut = WshShell.CreateShortcut(strDesktop & "\Automate.lnk")
oShortCut.TargetPath = strPath & "\Instalar_y_Lanzar.vbs"
oShortCut.WorkingDirectory = strPath
oShortCut.WindowStyle = 1
oShortCut.Description = "Iniciar Automate - Descarga de Planillas"
oShortCut.IconLocation = "shell32.dll, 14"
oShortCut.Save

' 2. Ejecutar el archivo start.bat en modo oculto (0)
' Esto permite que al hacer doble clic se instale/actualice y lance todo
WshShell.Run "cmd /c start.bat", 0, False
