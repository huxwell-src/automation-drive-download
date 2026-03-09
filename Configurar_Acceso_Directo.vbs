Set WshShell = CreateObject("WScript.Shell")
strDesktop = WshShell.SpecialFolders("Desktop")
strPath = WshShell.CurrentDirectory

' Crear el acceso directo en el escritorio
Set oShortCut = WshShell.CreateShortcut(strDesktop & "\Automate.lnk")
oShortCut.TargetPath = strPath & "\Lanzar_Automate.vbs"
oShortCut.WorkingDirectory = strPath
oShortCut.WindowStyle = 1
oShortCut.Description = "Iniciar Automate - Descarga de Planillas"

' Usar un icono de sistema (mundo/web)
' shell32.dll, 14 es un icono de mundo/internet en la mayoría de versiones de Windows
oShortCut.IconLocation = "shell32.dll, 14"

oShortCut.Save

MsgBox "¡Acceso directo creado en el escritorio con exito!", 64, "Automate Setup"
