$ffmpegUrl = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
$parentDir = Split-Path -Parent $PSScriptRoot
$destDir = Join-Path $parentDir "external"
$zipFile = Join-Path $destDir "ffmpeg.zip"
$extractPath = Join-Path $destDir "ffmpeg_temp"
$finalBinDir = Join-Path $destDir "ffmpeg"

if (-not (Test-Path $destDir)) {
    New-Item -ItemType Directory -Path $destDir
}

Write-Host "Downloading FFmpeg from $ffmpegUrl..."
Invoke-WebRequest -Uri $ffmpegUrl -OutFile $zipFile

Write-Host "Extracting FFmpeg..."
if (Test-Path $extractPath) { Remove-Item -Recurse -Force $extractPath }
Expand-Archive -Path $zipFile -DestinationPath $extractPath

# FFmpeg zip usually contains a single top-level folder
$topLevelDir = Get-ChildItem -Path $extractPath | Where-Object { $_.PSIsContainer } | Select-Object -First 1
$binSource = Join-Path $topLevelDir.FullName "bin"

if (-not (Test-Path $finalBinDir)) {
    New-Item -ItemType Directory -Path $finalBinDir
}

Write-Host "Moving binaries to $finalBinDir..."
Get-ChildItem -Path $binSource | Copy-Item -Destination $finalBinDir -Force

Write-Host "Cleaning up..."
if (Test-Path $zipFile) { Remove-Item -Path $zipFile -Force }
if (Test-Path $extractPath) { Remove-Item -Recurse -Force $extractPath }

Write-Host "FFmpeg installed successfully to $finalBinDir"
Write-Host "FFmpeg executable is at: $(Join-Path $finalBinDir 'ffmpeg.exe')"
