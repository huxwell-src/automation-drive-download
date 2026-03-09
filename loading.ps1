Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

# Configuración de colores (Paleta similar a la web)
$bgColor = [System.Drawing.Color]::FromArgb(251, 251, 253) # #FBFBFD
$textColor = [System.Drawing.Color]::FromArgb(29, 29, 31)   # #1D1D1F
$accentColor = [System.Drawing.Color]::FromArgb(0, 102, 204) # Azul Apple
$grayText = [System.Drawing.Color]::FromArgb(134, 134, 139) # #86868B

$form = New-Object System.Windows.Forms.Form
$form.Text = "Cargando Automate..."
$form.Size = New-Object System.Drawing.Size(450, 200)
$form.StartPosition = "CenterScreen"
$form.FormBorderStyle = "None" # Sin bordes de Windows
$form.BackColor = $bgColor
$form.TopMost = $true

# Crear bordes redondeados (Región)
$rect = New-Object System.Drawing.Rectangle(0, 0, $form.Width, $form.Height)
$path = New-Object System.Drawing.Drawing2D.GraphicsPath
$dim = 40
$path.AddArc(0, 0, $dim, $dim, 180, 90)
$path.AddArc($form.Width - $dim, 0, $dim, $dim, 270, 90)
$path.AddArc($form.Width - $dim, $form.Height - $dim, $dim, $dim, 0, 90)
$path.AddArc(0, $form.Height - $dim, $dim, $dim, 90, 90)
$path.CloseAllFigures()
$form.Region = New-Object System.Drawing.Region($path)

# Título Principal
$title = New-Object System.Windows.Forms.Label
$title.Text = "Drive Batch Processor"
$title.Size = New-Object System.Drawing.Size(400, 40)
$title.Location = New-Object System.Drawing.Point(25, 35)
$title.TextAlign = "MiddleCenter"
$title.ForeColor = $textColor
$title.Font = New-Object System.Drawing.Font("Segoe UI", 18, [System.Drawing.FontStyle]::Bold)

# Subtítulo / Estado
$subtitle = New-Object System.Windows.Forms.Label
$subtitle.Text = "Preparando entorno y servidores..."
$subtitle.Size = New-Object System.Drawing.Size(400, 25)
$subtitle.Location = New-Object System.Drawing.Point(25, 75)
$subtitle.TextAlign = "MiddleCenter"
$subtitle.ForeColor = $grayText
$subtitle.Font = New-Object System.Drawing.Font("Segoe UI", 10, [System.Drawing.FontStyle]::Regular)

# Panel para la barra de progreso (Estilo Apple)
$progressPanel = New-Object System.Windows.Forms.Panel
$progressPanel.Size = New-Object System.Drawing.Size(300, 6)
$progressPanel.Location = New-Object System.Drawing.Point(75, 120)
$progressPanel.BackColor = [System.Drawing.Color]::FromArgb(230, 230, 235)

# Barra de progreso real (Indicador animado)
$indicator = New-Object System.Windows.Forms.Panel
$indicator.Size = New-Object System.Drawing.Size(50, 6)
$indicator.Location = New-Object System.Drawing.Point(0, 0)
$indicator.BackColor = $accentColor

$progressPanel.Controls.Add($indicator)

# Timer para la animación de la barra
$timer = New-Object System.Windows.Forms.Timer
$timer.Interval = 15
$script:step = 4
$timer.Add_Tick({
    $newX = $indicator.Location.X + $script:step
    if ($newX -gt ($progressPanel.Width - $indicator.Width) -or $newX -lt 0) {
        $script:step = -$script:step
    }
    $indicator.Location = New-Object System.Drawing.Point($newX, 0)
})
$timer.Start()

$form.Controls.Add($title)
$form.Controls.Add($subtitle)
$form.Controls.Add($progressPanel)

# Permitir arrastrar la ventana sin bordes
$form.Add_MouseDown({
    if ($_.Button -eq [System.Windows.Forms.MouseButtons]::Left) {
        $script:dragging = $true
        $script:startPos = $_.Location
    }
})
$form.Add_MouseMove({
    if ($script:dragging) {
        $screenPos = $form.PointToScreen($_.Location)
        $form.Location = New-Object System.Drawing.Point($screenPos.X - $script:startPos.X, $screenPos.Y - $script:startPos.Y)
    }
})
$form.Add_MouseUp({ $script:dragging = $false })

$form.ShowDialog()
