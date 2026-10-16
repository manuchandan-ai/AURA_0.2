# ==============================================================================
#  AURA - Adaptive Unified Reasoning Assistant
#  Production Orchestration & Self-Healing Bootstrapper
# ==============================================================================

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
$Host.UI.RawUI.WindowTitle = "AURA Master Control Plane"
Clear-Host

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "       ⚛️  AURA INTELLIGENCE PLATFORM BOOTSTRAPPER         " -ForegroundColor Magenta
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ""

$AURA_DIR = $PSScriptRoot
if (-not $AURA_DIR) { $AURA_DIR = "D:\aura_1.0\aura_1.0" }
Set-Location -Path $AURA_DIR

# ------------------------------------------------------------------------------
# 1. KILL ORPHANED PROCESSES ON PORTS 8000 & 8501
# ------------------------------------------------------------------------------
Write-Host "[1/6] Scanning and releasing system network ports..." -ForegroundColor Yellow

function Free-Port([int]$Port) {
    $processes = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique
    foreach ($pid_val in $processes) {
        if ($pid_val -and $pid_val -ne 0) {
            Write-Host "      Killing stale process on port $Port (PID: $pid_val)..." -ForegroundColor DarkYellow
            Stop-Process -Id $pid_val -Force -ErrorAction SilentlyContinue
        }
    }
}

Free-Port 8000
Free-Port 8501
Start-Sleep -Seconds 1
Write-Host "      Ports 8000 and 8501 are clean." -ForegroundColor Green

# ------------------------------------------------------------------------------
# 2. VERIFY ARTIFACT STORAGE DIRECTORIES
# ------------------------------------------------------------------------------
Write-Host "[2/6] Verifying physical artifact repository paths..." -ForegroundColor Yellow
$STORAGE_PATH = Join-Path $AURA_DIR "artifacts_storage"
if (-not (Test-Path $STORAGE_PATH)) {
    New-Item -ItemType Directory -Path $STORAGE_PATH -Force | Out-Null
    Write-Host "      Created $STORAGE_PATH" -ForegroundColor Green
} else {
    Write-Host "      Storage repository intact." -ForegroundColor Green
}

# ------------------------------------------------------------------------------
# 3. SCHEMA MIGRATION SAFEGUARD
# ------------------------------------------------------------------------------
Write-Host "[3/6] Validating SQLite database schema and foreign keys..." -ForegroundColor Yellow
python -c "
import sqlite3, os
db_path = 'aura.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    def add_col(tbl, col):
        cur.execute(f'PRAGMA table_info({tbl})')
        cols = [r[1] for r in cur.fetchall()]
        if col.split()[0] not in cols:
            cur.execute(f'ALTER TABLE {tbl} ADD COLUMN {col}')
    add_col('users', 'freeze_tokens INTEGER DEFAULT 2')
    add_col('goals', 'saved_streak_count INTEGER DEFAULT 0')
    add_col('goals', 'in_recovery BOOLEAN DEFAULT 0')
    add_col('goals', 'recovery_task TEXT')
    conn.commit()
    conn.close()
"
Write-Host "      Database schema synchronized." -ForegroundColor Green

# ------------------------------------------------------------------------------
# 4. CHECK OLLAMA EMBEDDING ENGINE
# ------------------------------------------------------------------------------
Write-Host "[4/6] Auditing local AI runtime (Ollama)..." -ForegroundColor Yellow
try {
    $ollamaCheck = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -Method Get -TimeoutSec 2 -ErrorAction Stop
    $models = $ollamaCheck.models | ForEach-Object { $_.name }
    Write-Host "      Ollama active. Available models: $($models -join ', ')" -ForegroundColor Green
    if ($models -contains "nomic-embed-text:latest" -or $models -contains "nomic-embed-text") {
        Write-Host "      Vector RAG engine (nomic-embed-text) ready." -ForegroundColor Green
    } else {
        Write-Host "      Notice: nomic-embed-text not found. RAG fallback will use direct slicing." -ForegroundColor DarkYellow
    }
} catch {
    Write-Host "      Warning: Ollama offline. Cloud Groq API router will handle inference." -ForegroundColor DarkYellow
}

# ------------------------------------------------------------------------------
# 5. START FASTAPI BACKEND (DETACHED PROCESS)
# ------------------------------------------------------------------------------
Write-Host "[5/6] Booting FastAPI neural engine on port 8000..." -ForegroundColor Yellow
$BackendProcess = Start-Process -FilePath "python" -ArgumentList "-m uvicorn main:app --port 8000 --reload" -PassThru -NoNewWindow

# Wait for backend health poll
$maxRetries = 40
$isHealthy = $false
Write-Host "      Awaiting backend health synchronization..." -NoNewline

for ($i = 0; $i -lt $maxRetries; $i++) {
    Start-Sleep -Milliseconds 600
    try {
        $res = Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -Method Get -TimeoutSec 1 -ErrorAction SilentlyContinue
        if ($res.status -eq "online" -or $res.status -eq "degraded") {
            $isHealthy = $true
            break
        }
    } catch {
        Write-Host "." -NoNewline
    }
}
Write-Host ""

if (-not $isHealthy) {
    Write-Host "      [ERROR] FastAPI failed to report healthy within 24 seconds." -ForegroundColor Red
    Write-Host "      Stopping process $BackendProcess.Id" -ForegroundColor Red
    Stop-Process -Id $BackendProcess.Id -Force
    Exit 1
}

Write-Host "      FastAPI engine online and answering on http://127.0.0.1:8000." -ForegroundColor Green

# ------------------------------------------------------------------------------
# 6. OPEN UNIFIED AURA WEB APPLICATION & MONITOR
# ------------------------------------------------------------------------------
Write-Host "[6/6] Launching Unified AURA Neural Interface on port 8000..." -ForegroundColor Yellow
Write-Host ""
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  ✅ ALL AURA SUBSYSTEMS NOMINAL                          " -ForegroundColor Green
Write-Host "  👉 Modern Web App:    http://localhost:8000            " -ForegroundColor Cyan
Write-Host "  👉 Default Accounts:  admin/admin123 | john/operator123" -ForegroundColor DarkGray
Write-Host "  (Press Ctrl+C to terminate platform)                   " -ForegroundColor DarkGray
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ""

# Automatically open only the unified web app in default browser
Start-Process "http://localhost:8000"

try {
    # Keep orchestrator running and monitor backend
    Wait-Process -Id $BackendProcess.Id
} finally {
    Write-Host "`nShutting down backend process (PID: $($BackendProcess.Id))..." -ForegroundColor Yellow
    Stop-Process -Id $BackendProcess.Id -Force -ErrorAction SilentlyContinue
    Write-Host "AURA platform halted." -ForegroundColor Green
}