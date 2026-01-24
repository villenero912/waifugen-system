# update_github.ps1 - Script de actualización rápida a GitHub
# Uso: .\update_github.ps1 -Message "Tu mensaje de commit"
# Autor: WaifuGen Team
# Descripción: Automatiza el proceso de commit y push a GitHub

param(
    [Parameter(Mandatory = $false)]
    [string]$Message = "Update: Latest changes from Windows",
    
    [Parameter(Mandatory = $false)]
    [switch]$Force = $false
)

$ProjectPath = "C:\Users\Sebas\Downloads\package (1)\waifugen_system"

# Colores para mensajes
$ColorInfo = "Cyan"
$ColorSuccess = "Green"
$ColorWarning = "Yellow"
$ColorError = "Red"

Write-Host ""
Write-Host "==================================" -ForegroundColor $ColorInfo
Write-Host "  WaifuGen GitHub Update Tool" -ForegroundColor $ColorInfo
Write-Host "==================================" -ForegroundColor $ColorInfo
Write-Host ""

# Cambiar al directorio del proyecto
try {
    Set-Location $ProjectPath
    Write-Host "✓ Located project directory: $ProjectPath" -ForegroundColor $ColorSuccess
}
catch {
    Write-Host "✗ Error: Could not locate project directory" -ForegroundColor $ColorError
    Write-Host "  Path: $ProjectPath" -ForegroundColor $ColorError
    exit 1
}

Write-Host ""

# Verificar que estamos en un repositorio Git
$isGitRepo = Test-Path ".git"
if (-not $isGitRepo) {
    Write-Host "✗ Error: Not a Git repository" -ForegroundColor $ColorError
    exit 1
}

# Verificar conexión con remote
Write-Host "🔍 Checking Git remote..." -ForegroundColor $ColorInfo
$remote = git remote -v 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Error: No remote repository configured" -ForegroundColor $ColorError
    exit 1
}

Write-Host "✓ Remote configured:" -ForegroundColor $ColorSuccess
Write-Host "  $($remote | Select-Object -First 1)" -ForegroundColor Gray
Write-Host ""

# Verificar estado
Write-Host "📊 Repository Status:" -ForegroundColor $ColorInfo
Write-Host "──────────────────────" -ForegroundColor $ColorInfo
git status --short

# Verificar si hay cambios
$hasChanges = git status --short
if (-not $hasChanges) {
    Write-Host ""
    Write-Host "ℹ No changes to commit. Repository is up to date." -ForegroundColor $ColorWarning
    exit 0
}

Write-Host ""

# Mostrar archivos que se van a agregar
$untrackedFiles = git ls-files --others --exclude-standard
if ($untrackedFiles) {
    Write-Host "📝 Untracked files that will be added:" -ForegroundColor $ColorWarning
    foreach ($file in $untrackedFiles) {
        Write-Host "  + $file" -ForegroundColor Yellow
    }
    Write-Host ""
}

# Mostrar archivos modificados
$modifiedFiles = git ls-files --modified
if ($modifiedFiles) {
    Write-Host "✏️  Modified files:" -ForegroundColor $ColorWarning
    foreach ($file in $modifiedFiles) {
        Write-Host "  M $file" -ForegroundColor Yellow
    }
    Write-Host ""
}

# Confirmación del usuario
if (-not $Force) {
    Write-Host "Commit message: " -NoNewline -ForegroundColor $ColorInfo
    Write-Host "`"$Message`"" -ForegroundColor White
    Write-Host ""
    
    $confirm = Read-Host "Do you want to commit and push these changes? (y/n)"
    
    if ($confirm -ne 'y' -and $confirm -ne 'Y') {
        Write-Host "❌ Update cancelled by user." -ForegroundColor $ColorError
        exit 0
    }
}

Write-Host ""
Write-Host "🚀 Starting update process..." -ForegroundColor $ColorInfo
Write-Host ""

# Agregar todos los archivos
Write-Host "➕ Stage 1/3: Adding files..." -ForegroundColor $ColorInfo
git add .

if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Error adding files" -ForegroundColor $ColorError
    exit 1
}
Write-Host "✓ Files staged successfully" -ForegroundColor $ColorSuccess
Write-Host ""

# Commit
Write-Host "💾 Stage 2/3: Creating commit..." -ForegroundColor $ColorInfo
git commit -m "$Message"

if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Error creating commit" -ForegroundColor $ColorError
    exit 1
}
Write-Host "✓ Commit created successfully" -ForegroundColor $ColorSuccess
Write-Host ""

# Push
Write-Host "🌐 Stage 3/3: Pushing to GitHub..." -ForegroundColor $ColorInfo
git push origin master 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Error pushing to GitHub" -ForegroundColor $ColorError
    Write-Host ""
    Write-Host "Common solutions:" -ForegroundColor $ColorWarning
    Write-Host "  1. Check your internet connection" -ForegroundColor Gray
    Write-Host "  2. Verify GitHub token is valid" -ForegroundColor Gray
    Write-Host "  3. Pull latest changes first: git pull origin master" -ForegroundColor Gray
    exit 1
}

Write-Host "✓ Successfully pushed to GitHub!" -ForegroundColor $ColorSuccess
Write-Host ""

# Mostrar log de commits recientes
Write-Host "📜 Recent commits:" -ForegroundColor $ColorInfo
Write-Host "──────────────────" -ForegroundColor $ColorInfo
git log --oneline -5 --color=always

Write-Host ""
Write-Host "==================================" -ForegroundColor $ColorSuccess
Write-Host "  ✅ GitHub Update Complete!" -ForegroundColor $ColorSuccess
Write-Host "==================================" -ForegroundColor $ColorSuccess
Write-Host ""
Write-Host "Next steps:" -ForegroundColor $ColorInfo
Write-Host "  1. Verify changes on GitHub: https://github.com/villenero912/waifugen-system" -ForegroundColor Gray
Write-Host "  2. Deploy to VPS: .\scripts\manage_waifugen.ps1 -Action update" -ForegroundColor Gray
Write-Host ""
