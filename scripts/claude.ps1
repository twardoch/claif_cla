# PowerShell wrapper for Claude CLI
# Provides robust cross-platform execution on Windows

param(
    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]]$Arguments
)

# Function to find Claude executable
function Find-ClaudeExecutable {
    # Check CLAUDE_CLI_PATH environment variable
    if ($env:CLAUDE_CLI_PATH) {
        $candidates = @(
            Join-Path $env:CLAUDE_CLI_PATH "claude.cmd",
            Join-Path $env:CLAUDE_CLI_PATH "claude.exe",
            Join-Path $env:CLAUDE_CLI_PATH "claude.bat",
            $env:CLAUDE_CLI_PATH
        )
        
        foreach ($path in $candidates) {
            if (Test-Path $path) {
                return $path
            }
        }
    }
    
    # Search in PATH
    $claudeInPath = Get-Command -Name claude -ErrorAction SilentlyContinue
    if ($claudeInPath) {
        return $claudeInPath.Source
    }
    
    # Check common installation locations
    $searchPaths = @(
        "$env:APPDATA\npm\claude.cmd",
        "$env:APPDATA\npm\claude.exe",
        "$env:LOCALAPPDATA\Programs\claif\bin\claude.cmd",
        "$env:LOCALAPPDATA\Programs\claif\bin\claude.exe",
        "$env:LOCALAPPDATA\Programs\claif\bin\claude-bin\claude.exe",
        "$env:LOCALAPPDATA\Programs\claif\bin\claude-bin\claude",
        "$env:USERPROFILE\.local\bin\claude.cmd",
        "$env:USERPROFILE\.local\bin\claude.exe"
    )
    
    foreach ($path in $searchPaths) {
        if (Test-Path $path) {
            return $path
        }
    }
    
    # Check if npm is available and try to find via npm
    $npmCmd = Get-Command -Name npm -ErrorAction SilentlyContinue
    if ($npmCmd) {
        try {
            $npmRoot = & npm root -g 2>$null
            if ($npmRoot) {
                $npmClaude = Join-Path $npmRoot "..\@anthropic-ai\claude-code\bin\claude"
                if (Test-Path $npmClaude) {
                    return $npmClaude
                }
            }
        } catch {
            # Ignore npm errors
        }
    }
    
    # Check if bun is available
    $bunCmd = Get-Command -Name bun -ErrorAction SilentlyContinue
    if ($bunCmd) {
        try {
            $bunPath = & bun pm bin -g 2>$null
            if ($bunPath) {
                $bunClaude = Join-Path $bunPath "claude"
                if (Test-Path $bunClaude) {
                    return $bunClaude
                }
            }
        } catch {
            # Ignore bun errors
        }
    }
    
    return $null
}

# Main execution
$claudeExe = Find-ClaudeExecutable

if (-not $claudeExe) {
    Write-Error "Claude CLI not found."
    Write-Host ""
    Write-Host "Please install Claude CLI using one of these methods:"
    Write-Host "  npm install -g @anthropic-ai/claude-code"
    Write-Host "  bun add -g @anthropic-ai/claude-code"
    Write-Host "  claif install claude"
    Write-Host ""
    Write-Host "Or set CLAUDE_CLI_PATH environment variable to the installation directory."
    exit 1
}

# For bundled installations, change to claude-bin directory
$claudeBinDir = Join-Path $env:LOCALAPPDATA "Programs\claif\bin\claude-bin"
if (Test-Path $claudeBinDir) {
    try {
        Push-Location $claudeBinDir
        & "./claude" @Arguments
        exit $LASTEXITCODE
    } catch {
        Write-Error "Failed to execute Claude CLI from bundled directory: $_"
        exit 1
    } finally {
        Pop-Location
    }
} else {
    # Execute Claude directly
    try {
        & $claudeExe @Arguments
        exit $LASTEXITCODE
    } catch {
        Write-Error "Failed to execute Claude CLI: $_"
        exit 1
    }
}