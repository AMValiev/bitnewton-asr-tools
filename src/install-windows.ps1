# BitNewton ASR Tools - Ustanovka dlya Windows
# PowerShell Installation Script

# --- 1. Opredelyaem put k KORNYU proekta ---
# Poluchaem papku, gde lezhit etot skript (eto papka src)
$ScriptLocation = $PSScriptRoot

# Esli peremennaya pusta (fallback), berem put iz komandy zapuska
if (-not $ScriptLocation) {
    $ScriptLocation = Split-Path -Parent $MyInvocation.MyCommand.Path
}

# SAMAIA VAZHNAYA STROKA: Podnimaemsya na uroven vyshe (iz src v koren)
$InstallDir = Split-Path -Parent $ScriptLocation
# -------------------------------------------------------------

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Ustanovka BitNewton ASR Tools" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Papka ustanovki: $InstallDir" -ForegroundColor Gray
Write-Host ""

# Proverka na pustoy put (zashchita ot oshibki)
if ([string]::IsNullOrWhiteSpace($InstallDir)) {
    Write-Host "[ERROR] Ne udalos opredelit put ustanovki!" -ForegroundColor Red
    exit
}

Write-Host "[1/3] Opredelenie profilya PowerShell..." -ForegroundColor Yellow
Write-Host "Profil: $PROFILE" -ForegroundColor Gray

# Sozdaem papku dlya profilya, esli eyo net
$ProfileDir = Split-Path -Parent $PROFILE
if (-not (Test-Path $ProfileDir)) {
    New-Item -ItemType Directory -Path $ProfileDir -Force | Out-Null
}

# Sozdaem profil, esli ego net
if (-not (Test-Path $PROFILE)) {
    New-Item -ItemType File -Path $PROFILE -Force | Out-Null
    Write-Host "Sozdan fayl profilya" -ForegroundColor Green
}

Write-Host "[2/3] Obnovlenie puti v profile..." -ForegroundColor Yellow

# --- OCHISTKA I OBNOVLENIE ---
# 1. Chitaem fayl
$ProfileContent = Get-Content $PROFILE -Raw -ErrorAction SilentlyContinue
if (-not $ProfileContent) { $ProfileContent = "" }

# 2. Udalyaem starye versii blokov (RegEx)
# Ichtet tekst ot "# BitNewton..." do zakryvayushchey skobki "}"
$CleanPattern = '(?s)# BitNewton ASR Tools.*?summarize\.bat" @args\s*}'
$CleanedContent = $ProfileContent -replace $CleanPattern, ""
$CleanedContent = $CleanedContent.Trim()

# 3. Gotovim novyy blok
$NewBlock = @"

# BitNewton ASR Tools (Updated: $(Get-Date -Format "yyyy-MM-dd HH:mm"))
function transcribe {
    & "$InstallDir\bin\transcribe.bat" @args
}

function summarize {
    & "$InstallDir\bin\summarize.bat" @args
}
"@

# 4. Zapisyvaem obratno (Staryy chistyy kontent + Novyy blok)
Set-Content -Path $PROFILE -Value ($CleanedContent + $NewBlock) -Force

Write-Host "Profil uspeshno obnovlen! Starye zapisi vychishcheny." -ForegroundColor Green
Write-Host "Aktualnyy put: $InstallDir" -ForegroundColor Green
# -----------------------------

Write-Host "[3/3] Proverka ustanovki Python..." -ForegroundColor Yellow

# Proveryaem embedded Python
$EmbeddedPython = Join-Path $InstallDir "python\python.exe"

if (Test-Path $EmbeddedPython) {
    # Pytayemsya zapustit, chtoby poluchit versiyu
    try {
        $Version = & $EmbeddedPython --version 2>&1
        Write-Host "Embedded Python nayden: $Version" -ForegroundColor Green
    } catch {
         Write-Host "Embedded Python est, no ne zapuskaetsya." -ForegroundColor Red
    }
} else {
    # Proveryaem sistemnyy Python
    try {
        $Version = python --version 2>&1
        Write-Host "Sistemnyy Python nayden: $Version" -ForegroundColor Green
    } catch {
        Write-Host "Python ne nayden!" -ForegroundColor Red
        Write-Host ""
        Write-Host "Ustanovite Python:" -ForegroundColor Yellow
        Write-Host "https://www.python.org/downloads/" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Ustanovka zavershena!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Dostupnye komandy:" -ForegroundColor White
Write-Host "  - transcribe" -ForegroundColor Green
Write-Host "  - summarize" -ForegroundColor Green
Write-Host ""
Write-Host "VAZHNO: Perezapustite PowerShell ili vypolnite: . `$PROFILE" -ForegroundColor Yellow
Write-Host ""
Write-Host "Nazhmite lyubuyu klavishu dlya vykhoda..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")