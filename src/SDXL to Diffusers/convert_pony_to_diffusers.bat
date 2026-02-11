@echo off
setlocal EnableExtensions EnableDelayedExpansion
title [SDXL] Convert .safetensors -> Diffusers (stable logging)

rem ── Optional flag: --debug
set "DEBUG="
if /I "%~1"=="--debug" set "DEBUG=1"

rem ── Resolve ROOT
set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"

rem ── Prefer venv python
set "PYEXE="
if exist "%ROOT%\venv\Scripts\python.exe" set "PYEXE=%ROOT%\venv\Scripts\python.exe"
if not defined PYEXE for %%P in (python.exe) do (set "PYEXE=%%~f$PATH:P")
if not defined PYEXE (
  echo [FAIL] Python not found. Activate your venv or install Python.
  call :_keep_open 2
  exit /b 2
)

set "LOGDIR=%ROOT%\logs"
set "TMPDIR=%ROOT%\logs\tmp"
mkdir "%LOGDIR%" 2>nul
mkdir "%TMPDIR%" 2>nul

set "STAMP=%DATE:~-4%%DATE:~4,2%%DATE:~7,2%_%TIME: =0%"
set "STAMP=%STAMP::=%"
set "LOGFILE=%LOGDIR%\convert_%STAMP%.log"

echo [BOOT] %DATE% %TIME% > "%LOGFILE%"
echo [INFO] PYEXE=%PYEXE% >> "%LOGFILE%"
set "PYTHONUNBUFFERED=1"

echo.
echo === SDXL Checkpoint -> Diffusers Conversion ===
echo You can paste paths WITH or WITHOUT quotes. I'll normalize them.
echo Logs: %LOGFILE%
echo.

set "CKPT="
set "OUTDIR="
set "VAE="
set "USE_FP16=1"

set /p CKPT="Path to .safetensors checkpoint: "
set "CKPT=%CKPT:"=%"

if not exist "%CKPT%" (
  echo [FAIL] File not found: %CKPT%
  echo [FAIL] File not found: %CKPT% >> "%LOGFILE%"
  call :_keep_open 1
  exit /b 1
)

for %%X in ("%CKPT%") do set "EXT=%%~xX"
if /I not "%EXT%"==".safetensors" (
  echo [FAIL] Expecting a .safetensors file. Got: %CKPT%
  echo [FAIL] Expecting a .safetensors file. Got: %CKPT% >> "%LOGFILE%"
  call :_keep_open 1
  exit /b 1
)

set /p OUTDIR="Output folder for Diffusers model (will be created): "
set "OUTDIR=%OUTDIR:"=%"
if not defined OUTDIR (
  echo [FAIL] Output folder not specified.
  echo [FAIL] Output folder not specified. >> "%LOGFILE%"
  call :_keep_open 1
  exit /b 1
)

set /p VAE="(Optional) SDXL VAE (Diffusers folder or HF repo id) [Enter to skip]: "
set "VAE=%VAE:"=%"

echo.
echo [INFO] CKPT="%CKPT%"
echo [INFO] OUTDIR="%OUTDIR%"
if defined VAE echo [INFO] VAE="%VAE%"
echo [INFO] FP16 save: %USE_FP16%
if defined DEBUG echo [INFO] DEBUG: on
echo.

rem Ensure OUTDIR is a proper directory
if exist "%OUTDIR%" (
  if exist "%OUTDIR%\." (
    rem ok
  ) else (
    echo [WARN] "%OUTDIR%" exists and is a file. Choose a different output folder.
    echo [WARN] Output exists and is a file: %OUTDIR% >> "%LOGFILE%"
    call :_keep_open 1
    exit /b 1
  )
) else (
  mkdir "%OUTDIR%" 2>nul
  if errorlevel 1 (
    echo [FAIL] Could not create output folder: "%OUTDIR%"
    echo [FAIL] Could not create output folder: "%OUTDIR%" >> "%LOGFILE%"
    call :_keep_open 1
    exit /b 1
  )
)

rem ── Build flags
set "DBGFLAG="
if defined DEBUG set "DBGFLAG=--debug"

set "FP16FLAG="
if defined USE_FP16 set "FP16FLAG=--fp16"

set "VAEFLAG="
if defined VAE set "VAEFLAG=--vae \"%VAE%\""

echo [RUN] "%PYEXE%" "%ROOT%\convert_sdxl_ckpt_to_diffusers.py" --ckpt "%CKPT%" --out "%OUTDIR%" %DBGFLAG% %FP16FLAG% %VAEFLAG%
echo [RUN] %DATE% %TIME% :: %PYEXE% convert_sdxl_ckpt_to_diffusers.py --ckpt "%CKPT%" --out "%OUTDIR%" %DBGFLAG% %FP16FLAG% %VAEFLAG% >> "%LOGFILE%"

rem ── Stream to console AND log (simple, robust)
where powershell >nul 2>&1
if %ERRORLEVEL%==0 (
  "%PYEXE%" "%ROOT%\convert_sdxl_ckpt_to_diffusers.py" --ckpt "%CKPT%" --out "%OUTDIR%" %DBGFLAG% %FP16FLAG% %VAEFLAG% 2>&1 ^
    | powershell -NoLogo -NoProfile -Command "Tee-Object -FilePath '%LOGFILE%' -Append"
) else (
  rem fallback: console only + log append at the end
  "%PYEXE%" "%ROOT%\convert_sdxl_ckpt_to_diffusers.py" --ckpt "%CKPT%" --out "%OUTDIR%" %DBGFLAG% %FP16FLAG% %VAEFLAG%" 1>>"%LOGFILE%" 2>&1
)

set "RC=%ERRORLEVEL%"

rem Sanity check
if "%RC%"=="0" if not exist "%OUTDIR%\model_index.json" (
  echo [WARN] model_index.json not found in "%OUTDIR%".
  echo [WARN] model_index.json not found in "%OUTDIR%". >> "%LOGFILE%"
  set "RC=1"
)

if not "%RC%"=="0" (
  echo.
  echo [FAIL] Conversion failed (code %RC%). Log:
  echo        %LOGFILE%
  call :_open_log_prompt
  call :_keep_open %RC%
  exit /b %RC%
)

echo.
echo [OK] Converted successfully -> "%OUTDIR%"
echo [OK] model_index.json present.
echo Next: set "base_model" in training_config.json to:
echo   %OUTDIR%
call :_keep_open 0
exit /b 0

:_open_log_prompt
  set "ANS="
  set /p ANS="Open log in Notepad? (y/N): "
  if /I "%ANS%"=="Y" start notepad "%LOGFILE%"
  goto :eof

:_keep_open
  set "EXITCODE=%~1"
  echo.
  echo Press any key to close... (exit code %EXITCODE%)
  pause >nul
  rem If launched via double-click with /c, keep a shell open:
  if /I not "%CMDCMDLINE:/c=%"=="%CMDCMDLINE%" (
    cmd /k
  )
  goto :eof
