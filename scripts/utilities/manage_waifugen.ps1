# WaifuGen - Remote Management Script for Windows
# Purpose: Simplify VPS management via SSH/PowerShell

param (
    [Parameter(Mandatory=$false)]
    [string]$Action,

    [Parameter(Mandatory=$false)]
    [string]$Service = "all"
)

# Configuration - EDIT THESE VALUES
$VPS_IP = "YOUR_SERVER_IP"
$VPS_USER = "root" # or your sudo user
$REMOTE_DIR = "~/waifugen-system"

function Show-Help {
    Write-Host "Usage: .\manage_waifugen.ps1 -Action <Action> [-Service <ServiceName>]" -ForegroundColor Cyan
    Write-Host "`nActions:"
    Write-Host "  connect    - Open SSH session to VPS"
    Write-Host "  status     - Check Docker container status"
    Write-Host "  logs       - View logs (default: all services)"
    Write-Host "  restart    - Restart services (default: all)"
    Write-Host "  update     - Pull latest changes and restart"
    Write-Host "  check      - Run security/system health check"
}

if (-not $Action) {
    Show-Help
    exit
}

$RemoteCmd = ""

switch ($Action) {
    "connect" {
        ssh "$VPS_USER@$VPS_IP"
        exit
    }
    "status" {
        $RemoteCmd = "cd $REMOTE_DIR && docker compose ps"
    }
    "logs" {
        if ($Service -eq "all") {
            $RemoteCmd = "cd $REMOTE_DIR && docker compose logs -f --tail 100"
        } else {
            $RemoteCmd = "cd $REMOTE_DIR && docker compose logs -f --tail 100 $Service"
        }
    }
    "restart" {
        if ($Service -eq "all") {
            $RemoteCmd = "cd $REMOTE_DIR && docker compose restart"
        } else {
            $RemoteCmd = "cd $REMOTE_DIR && docker compose restart $Service"
        }
    }
    "update" {
        $RemoteCmd = "cd $REMOTE_DIR && git pull && docker compose up -d"
    }
    "check" {
        $RemoteCmd = "df -h && free -m && docker stats --no-stream"
    }
    Default {
        Write-Host "Error: Invalid Action '$Action'" -ForegroundColor Red
        Show-Help
        exit
    }
}

# Execute Remote Command
Write-Host ">>> Executing $Action on $VPS_IP..." -ForegroundColor Blue
ssh "$VPS_USER@$VPS_IP" "$RemoteCmd"
