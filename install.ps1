#Requires -Version 5.1
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ProjectDir = $PSScriptRoot
$BinDir = "$env:USERPROFILE\.local\bin"

Write-Host "checking requirements..."

# Python 3.10+
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Error "error: python not found — install Python 3.10+ from https://python.org"
    exit 1
}
python -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" 2>$null
if ($LASTEXITCODE -ne 0) {
    $pyVer = python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
    Write-Error "error: Python 3.10+ required, found Python $pyVer"
    exit 1
}
$pyVer = python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
Write-Host "  python: ok ($pyVer)"

# NTFS Alternate Data Streams support
$adsTest = python -c @"
import os, tempfile, sys
f = tempfile.NamedTemporaryFile(delete=False, suffix='.txt')
f.close()
try:
    with open(f.name + ':filecomment', 'w') as s:
        s.write('test')
    os.remove(f.name + ':filecomment')
    os.remove(f.name)
except Exception as e:
    try: os.remove(f.name)
    except: pass
    print(str(e), file=sys.stderr)
    sys.exit(1)
"@ 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Error "error: filesystem does not support Alternate Data Streams (NTFS required)`n       $adsTest"
    exit 1
}
Write-Host "  ads (ntfs): ok"

Write-Host ""

# Create BinDir
New-Item -ItemType Directory -Force -Path $BinDir | Out-Null

# Write Python runner scripts (path baked in at install time)
Set-Content -Path "$BinDir\cmt_run.py" -Encoding UTF8 -Value @"
import sys
sys.path.insert(0, r'$ProjectDir')
from filecomments.cli import main
main()
"@

Set-Content -Path "$BinDir\lsc_run.py" -Encoding UTF8 -Value @"
import sys
sys.path.insert(0, r'$ProjectDir')
from filecomments.cls import main
main()
"@

# Write .bat launchers
Set-Content -Path "$BinDir\cmt.bat" -Encoding ASCII -Value "@echo off`npython `"%~dp0cmt_run.py`" %*"
Set-Content -Path "$BinDir\lsc.bat"  -Encoding ASCII -Value "@echo off`npython `"%~dp0lsc_run.py`" %*"

Write-Host "installed: $BinDir\cmt.bat"
Write-Host "installed: $BinDir\lsc.bat"
Write-Host "note: the listing command is 'lsc' on Windows ('cls' is a built-in)"

# Add BinDir to user PATH if missing
$userPath = [Environment]::GetEnvironmentVariable("PATH", "User")
if ($userPath -notlike "*$BinDir*") {
    [Environment]::SetEnvironmentVariable("PATH", "$userPath;$BinDir", "User")
    Write-Host ""
    Write-Host "added $BinDir to user PATH — restart your terminal to activate"
}

Write-Host ""
Write-Host "done — re-run this script if you move the project directory"
