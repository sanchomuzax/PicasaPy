param(
    [Parameter(Mandatory = $true)][string]$Installer,
    [Parameter(Mandatory = $true)][string]$InstallDir,
    [Parameter(Mandatory = $true)][string]$LegacyExe
)

$ErrorActionPreference = "Stop"
$script:_elso_indulas_hatar_mp = 5.0
$script:_elso_induloablak_hatar_mp = 3.0

Add-Type -TypeDefinition @'
using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Text;

public sealed class PicasaPyWindow
{
    public IntPtr Handle;
    public IntPtr TopLevelHandle;
    public int ProcessId;
    public bool IsTopLevel;
    public string Text;
    public string ClassName;
    public bool Visible;
    public bool Enabled;
    public int Width;
    public int Height;
}

public static class PicasaPyNative
{
    public static string LastClickError = "";

    private delegate bool EnumWindowsProc(IntPtr hwnd, IntPtr lParam);

    [StructLayout(LayoutKind.Sequential)]
    private struct RECT { public int Left, Top, Right, Bottom; }

    [StructLayout(LayoutKind.Sequential)]
    private struct MOUSEINPUT
    {
        public int dx, dy;
        public uint mouseData, dwFlags, time;
        public UIntPtr dwExtraInfo;
    }

    [StructLayout(LayoutKind.Sequential)]
    private struct INPUT { public uint type; public MOUSEINPUT mi; }

    [DllImport("user32.dll", SetLastError = true)]
    private static extern bool EnumWindows(EnumWindowsProc callback, IntPtr lParam);
    [DllImport("user32.dll", SetLastError = true)]
    private static extern bool EnumChildWindows(IntPtr parent, EnumWindowsProc callback, IntPtr lParam);
    [DllImport("user32.dll", SetLastError = true)]
    private static extern uint GetWindowThreadProcessId(IntPtr hwnd, out uint processId);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)]
    private static extern int GetWindowTextW(IntPtr hwnd, StringBuilder text, int maxCount);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)]
    private static extern int GetClassNameW(IntPtr hwnd, StringBuilder text, int maxCount);
    [DllImport("user32.dll")]
    private static extern bool IsWindowVisible(IntPtr hwnd);
    [DllImport("user32.dll")]
    private static extern bool IsWindowEnabled(IntPtr hwnd);
    [DllImport("user32.dll")]
    private static extern bool GetWindowRect(IntPtr hwnd, out RECT rect);
    [DllImport("user32.dll", SetLastError = true)]
    private static extern bool SetCursorPos(int x, int y);
    [DllImport("user32.dll", SetLastError = true)]
    private static extern uint SendInput(uint count, INPUT[] inputs, int size);

    private static PicasaPyWindow Describe(IntPtr hwnd, IntPtr topLevel, bool isTopLevel, uint processId)
    {
        var text = new StringBuilder(512);
        var className = new StringBuilder(256);
        GetWindowTextW(hwnd, text, text.Capacity);
        GetClassNameW(hwnd, className, className.Capacity);
        RECT rect;
        GetWindowRect(hwnd, out rect);
        return new PicasaPyWindow {
            Handle = hwnd,
            TopLevelHandle = topLevel,
            ProcessId = (int)processId,
            IsTopLevel = isTopLevel,
            Text = text.ToString(),
            ClassName = className.ToString(),
            Visible = IsWindowVisible(hwnd),
            Enabled = IsWindowEnabled(hwnd),
            Width = Math.Max(0, rect.Right - rect.Left),
            Height = Math.Max(0, rect.Bottom - rect.Top)
        };
    }

    public static PicasaPyWindow[] AllWindows()
    {
        var result = new List<PicasaPyWindow>();
        EnumWindows((top, _) => {
            uint pid;
            GetWindowThreadProcessId(top, out pid);
            result.Add(Describe(top, top, true, pid));
            EnumChildWindows(top, (child, __) => {
                uint childPid;
                GetWindowThreadProcessId(child, out childPid);
                result.Add(Describe(child, top, false, childPid));
                return true;
            }, IntPtr.Zero);
            return true;
        }, IntPtr.Zero);
        return result.ToArray();
    }

    public static PicasaPyWindow[] ForProcess(int targetPid)
    {
        var result = new List<PicasaPyWindow>();
        foreach (var window in AllWindows())
            if (window.ProcessId == targetPid) result.Add(window);
        return result.ToArray();
    }

    public static bool ClickPhysical(IntPtr hwnd)
    {
        RECT rect;
        if (!GetWindowRect(hwnd, out rect))
        {
            LastClickError = "GetWindowRect Win32 hibakód: " + Marshal.GetLastWin32Error();
            return false;
        }
        if (rect.Right <= rect.Left || rect.Bottom <= rect.Top)
        {
            LastClickError = "a vezérlő ablakmérete üres";
            return false;
        }
        if (!SetCursorPos((rect.Left + rect.Right) / 2, (rect.Top + rect.Bottom) / 2))
        {
            LastClickError = "SetCursorPos Win32 hibakód: " + Marshal.GetLastWin32Error();
            return false;
        }
        const uint inputMouse = 0;
        const uint leftDown = 0x0002;
        const uint leftUp = 0x0004;
        var inputs = new[] {
            new INPUT { type = inputMouse, mi = new MOUSEINPUT { dwFlags = leftDown } },
            new INPUT { type = inputMouse, mi = new MOUSEINPUT { dwFlags = leftUp } }
        };
        uint sent = SendInput((uint)inputs.Length, inputs, Marshal.SizeOf(typeof(INPUT)));
        if (sent != inputs.Length)
        {
            LastClickError = string.Format(
                "SendInput {0}/{1} bemenetet küldött, Win32 hibakód: {2}",
                sent, inputs.Length, Marshal.GetLastWin32Error());
            return false;
        }
        LastClickError = "";
        return true;
    }

}
'@

function Normalize-Caption([string]$Text) {
    return ($Text -replace "&", "").Trim()
}

function Get-WindowSnapshot([PicasaPyWindow[]]$Windows) {
    $topWindows = @($Windows | Where-Object { $_.IsTopLevel -and $_.Visible } |
        Sort-Object ProcessId, ClassName, Text)
    if ($topWindows.Count -eq 0) { return "<nincs látható felső szintű ablak>" }

    $lines = foreach ($top in $topWindows) {
        $buttons = @($Windows | Where-Object {
            -not $_.IsTopLevel -and $_.TopLevelHandle.ToInt64() -eq $top.Handle.ToInt64() -and
            $_.Visible -and $_.ClassName -match "Button" -and (Normalize-Caption $_.Text)
        } | ForEach-Object {
            "$($_.ClassName):$(Normalize-Caption $_.Text)"
        } | Sort-Object)
        $buttonText = if ($buttons.Count) { $buttons -join ", " } else { "<nincs gomb>" }
        "PID=$($top.ProcessId) class='$($top.ClassName)' title='$($top.Text)' buttons=[$buttonText]"
    }
    return $lines -join [Environment]::NewLine
}

function Write-WindowSnapshotIfChanged([PicasaPyWindow[]]$Windows) {
    $snapshot = Get-WindowSnapshot $Windows
    if ($snapshot -ne $script:_utolsoMegfigyeltAllapot) {
        $script:_utolsoMegfigyeltAllapot = $snapshot
        $script:_fuggoAllapot = $snapshot
    }

    $now = [DateTimeOffset]::UtcNow
    if ($null -ne $script:_fuggoAllapot -and
        ($now - $script:_utolsoDiagnosztika).TotalSeconds -ge 1) {
        if ($script:_fuggoAllapot -ne $script:_utolsoKiirtAllapot) {
            Write-Host "Telepítőablak-állapot:`n$($script:_fuggoAllapot)"
            $script:_utolsoKiirtAllapot = $script:_fuggoAllapot
        }
        $script:_fuggoAllapot = $null
        $script:_utolsoDiagnosztika = $now
    }
}

function Save-FailureScreenshot {
    try {
        Add-Type -AssemblyName System.Drawing
        Add-Type -AssemblyName System.Windows.Forms
        if (-not (Test-Path -LiteralPath $script:_screenshotDirectory)) {
            New-Item -ItemType Directory -Force -Path $script:_screenshotDirectory | Out-Null
        }
        $screen = [System.Windows.Forms.SystemInformation]::VirtualScreen
        if ($screen.Width -le 0 -or $screen.Height -le 0) {
            throw "nem érhető el képernyőterület"
        }
        $bitmap = [System.Drawing.Bitmap]::new($screen.Width, $screen.Height)
        $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
        try {
            $graphics.CopyFromScreen($screen.Left, $screen.Top, 0, 0, $bitmap.Size)
            $script:_screenshotPath = Join-Path $script:_screenshotDirectory (
                "telepito-hiba-{0}.png" -f (Get-Date -Format "yyyyMMdd-HHmmss")
            )
            $bitmap.Save($script:_screenshotPath, [System.Drawing.Imaging.ImageFormat]::Png)
            Write-Host "Hibaképernyőkép: $($script:_screenshotPath)"
        } finally {
            $graphics.Dispose()
            $bitmap.Dispose()
        }
    } catch {
        Write-Warning "A képernyőkép mentése nem sikerült: $($_.Exception.Message)"
    }
}

function Get-CurrentUserUninstallEntry {
    $key = "Software\Microsoft\Windows\CurrentVersion\Uninstall\{9F3C1D28-7C4E-4E2B-9A55-3B1D6A0C77E1}_is1"
    foreach ($view in @([Microsoft.Win32.RegistryView]::Registry32, [Microsoft.Win32.RegistryView]::Registry64)) {
        $base = [Microsoft.Win32.RegistryKey]::OpenBaseKey([Microsoft.Win32.RegistryHive]::CurrentUser, $view)
        try {
            $entry = $base.OpenSubKey($key)
            if ($entry) {
                $entry.Dispose()
                return $true
            }
        } finally {
            $base.Dispose()
        }
    }
    return $false
}

$script:_runnerTemp = if ($env:RUNNER_TEMP) { $env:RUNNER_TEMP } else { $env:TEMP }
$script:_screenshotDirectory = Join-Path $script:_runnerTemp "PicasaPy-update-screenshots"
$script:_screenshotPath = $null
$script:_utolsoMegfigyeltAllapot = $null
$script:_utolsoKiirtAllapot = $null
$script:_fuggoAllapot = $null
$script:_utolsoDiagnosztika = [DateTimeOffset]::UtcNow.AddSeconds(-1)
$setup = $null
$app = $null

try {
    $installer = (Resolve-Path $Installer).Path
    $installDir = [IO.Path]::GetFullPath($InstallDir)
    $legacyExe = [IO.Path]::GetFullPath($LegacyExe)
    $executable = Join-Path $installDir "PicasaPy.exe"
    $profile = Join-Path $script:_runnerTemp "PicasaPy-first-click-profile"
    $local = Join-Path $profile "AppData\Local"
    $roaming = Join-Path $profile "AppData\Roaming"
    $temporary = Join-Path $profile "Temp"
    New-Item -ItemType Directory -Force -Path $local, $roaming, $temporary, $script:_screenshotDirectory | Out-Null
    $env:USERPROFILE = $profile
    $env:LOCALAPPDATA = $local
    $env:APPDATA = $roaming
    $env:TEMP = $temporary
    $env:TMP = $temporary
    $env:PICASAPY_LANG = "en"
    Remove-Item Env:QT_QPA_PLATFORM -ErrorAction SilentlyContinue
    Remove-Item Env:QT_QUICK_BACKEND -ErrorAction SilentlyContinue

    $currentProcess = [Diagnostics.Process]::GetCurrentProcess()
    Write-Host ("Valódi interaktív kattintás: UserInteractive={0}, session={1}" -f
        [Environment]::UserInteractive, $currentProcess.SessionId)
    $currentProcess.Dispose()
    $setup = Start-Process -FilePath $installer -ArgumentList @(
        "/SP-", "/NORESTART", "/ALLUSERS", "/DIR=$installDir"
    ) -PassThru
    Write-Host "Az Inno Setup indítófolyamatának PID-je: $($setup.Id); a varázslót minden felső szintű ablak között keresem."
    $setupDeadline = [DateTimeOffset]::UtcNow.AddMinutes(4)
    $finishClickedAt = $null
    $lastActionSignature = $null

    while ([DateTimeOffset]::UtcNow -lt $setupDeadline) {
        $windows = [PicasaPyNative]::AllWindows()
        Write-WindowSnapshotIfChanged $windows
        $wizard = $windows | Where-Object {
            $_.IsTopLevel -and $_.Visible -and $_.ClassName -eq "TWizardForm"
        } | Select-Object -First 1
        if (-not $wizard) {
            Start-Sleep -Milliseconds 100
            continue
        }

        $wizardControls = @($windows | Where-Object {
            $_.TopLevelHandle.ToInt64() -eq $wizard.Handle.ToInt64()
        } | ForEach-Object {
            "$($_.ClassName):$(Normalize-Caption $_.Text):enabled=$($_.Enabled)"
        } | Sort-Object)
        $stateSignature = "wizard:$($wizard.Text)|$($wizardControls -join '|')"
        # A varázsló „Select Destination Location” lapja is említi a „different folder”-t
        # (Browse...), ezért csak a varázslón KÍVÜLI ablak egyedi üzenetére figyelünk
        # (picasapy.iss: RemoveOtherInstallation).
        $folderPrompt = $windows | Where-Object {
            $_.Visible -and $_.TopLevelHandle.ToInt64() -ne $wizard.Handle.ToInt64() -and
            (Normalize-Caption $_.Text) -match "installed in a different folder|másik mappába telepített PicasaPy"
        } | Select-Object -First 1
        if ($folderPrompt) {
            $promptTop = $windows | Where-Object {
                $_.IsTopLevel -and $_.Handle.ToInt64() -eq $folderPrompt.TopLevelHandle.ToInt64()
            } | Select-Object -First 1
            if (-not $promptTop) { throw "a másik mappás megerősítő ablak felső szintű ablaka nem található" }
            $yes = $windows | Where-Object {
                -not $_.IsTopLevel -and $_.TopLevelHandle.ToInt64() -eq $promptTop.Handle.ToInt64() -and
                $_.Visible -and $_.Enabled -and $_.ClassName -match "Button" -and
                (Normalize-Caption $_.Text) -match "^(Yes|Igen)$"
            } | Select-Object -First 1
            if (-not $yes) { throw "a másik mappáról szóló megerősítésnél nem található a Yes/Igen gomb" }
            $promptControls = @($windows | Where-Object {
                $_.TopLevelHandle.ToInt64() -eq $promptTop.Handle.ToInt64()
            } | ForEach-Object {
                "$($_.ClassName):$(Normalize-Caption $_.Text):enabled=$($_.Enabled)"
            } | Sort-Object)
            $promptSignature = "prompt:$($promptTop.Text)|$($promptControls -join '|')"
            if ($promptSignature -ne $lastActionSignature) {
                if (-not [PicasaPyNative]::ClickPhysical($yes.Handle)) {
                    throw "a másik mappás jóváhagyásnál a valódi egérkattintás sikertelen volt: $([PicasaPyNative]::LastClickError)"
                }
                $lastActionSignature = $promptSignature
            }
            Start-Sleep -Milliseconds 100
            continue
        }
        $captions = @($windows | ForEach-Object { Normalize-Caption $_.Text })
        if (($captions -join " ") -match "could not be uninstalled|eltávolítása nem sikerült") {
            throw "a régi PicasaPy eltávolítása nem sikerült"
        }

        $buttons = @($windows | Where-Object {
            -not $_.IsTopLevel -and $_.TopLevelHandle.ToInt64() -eq $wizard.Handle.ToInt64() -and
            $_.Visible -and $_.Enabled -and $_.ClassName -match "Button"
        })
        $finish = $buttons | Where-Object {
            (Normalize-Caption $_.Text) -match "^(Finish|Befejezés)$"
        } | Select-Object -First 1
        if ($finish -and $stateSignature -ne $lastActionSignature) {
            if (-not [PicasaPyNative]::ClickPhysical($finish.Handle)) {
                throw "a telepítő Befejezés gombjára nem sikerült valódi egérkattintást küldeni: $([PicasaPyNative]::LastClickError)"
            }
            $finishClickedAt = [DateTimeOffset]::UtcNow
            break
        }

        if ($stateSignature -ne $lastActionSignature) {
            $next = $buttons | Where-Object {
                (Normalize-Caption $_.Text) -match "^(Next|Tovább)\s*>?$"
            } | Select-Object -First 1
            if (-not $next) {
                $next = $buttons | Where-Object {
                    (Normalize-Caption $_.Text) -match "^(Install|Telepítés)$"
                } | Select-Object -First 1
            }
            if ($next) {
                if (-not [PicasaPyNative]::ClickPhysical($next.Handle)) {
                    throw "a telepítő következő oldalára nem sikerült valódi egérkattintással továbblépni: $([PicasaPyNative]::LastClickError)"
                }
                $lastActionSignature = $stateSignature
            }
        }
        Start-Sleep -Milliseconds 100
    }

    if (-not $finishClickedAt) { throw "4 perc alatt nem jelent meg a Befejezés gomb" }
    if (-not (Test-Path $executable)) { throw "a telepítés után hiányzik a PicasaPy.exe" }

    $appDeadline = [DateTimeOffset]::UtcNow.AddSeconds(30)
    while ([DateTimeOffset]::UtcNow -lt $appDeadline) {
        $app = Get-Process -Name "PicasaPy" -ErrorAction SilentlyContinue |
            Where-Object {
                $_.Path -and $_.Path.Equals($executable, [StringComparison]::OrdinalIgnoreCase) -and
                $_.StartTime.ToUniversalTime() -ge $finishClickedAt.UtcDateTime.AddSeconds(-2)
            } | Select-Object -First 1
        if ($app) { break }
        Start-Sleep -Milliseconds 50
    }
    if (-not $app) { throw "a bepipált PicasaPy indítása nem jött létre a Befejezés kattintása után" }
    $appStart = [DateTimeOffset]$app.StartTime.ToUniversalTime()

    $visibleDeadline = [DateTimeOffset]::UtcNow.AddSeconds(10)
    $firstVisible = $null
    while ([DateTimeOffset]::UtcNow -lt $visibleDeadline) {
        $firstVisible = [PicasaPyNative]::ForProcess($app.Id) | Where-Object {
            $_.Visible -and $_.Width -gt 100 -and $_.Height -gt 100 -and
            ($_.ClassName -eq "TkTopLevel" -or $_.ClassName -eq "Tk" -or $_.Text -like "PicasaPy startup*")
        } | Select-Object -First 1
        if ($firstVisible) { break }
        Start-Sleep -Milliseconds 50
    }
    if (-not $firstVisible) { throw "a PicasaPy indulóablaka 10 másodperc alatt sem vált láthatóvá" }
    $induloablakMp = ([DateTimeOffset]::UtcNow - $appStart).TotalMilliseconds
    Write-Output ("Első látható indulóablak: {0:N0} ms" -f $induloablakMp)
    if ($induloablakMp -gt ($script:_elso_induloablak_hatar_mp * 1000)) {
        throw "az indulóablak lassan jelent meg: $([Math]::Round($induloablakMp)) ms; határ: $($script:_elso_induloablak_hatar_mp * 1000) ms"
    }

    $log = Join-Path $local "PicasaPy\errorlog.txt"
    $readyDeadline = [DateTimeOffset]::UtcNow.AddSeconds(120)
    $readyAt = $null
    while ([DateTimeOffset]::UtcNow -lt $readyDeadline) {
        if (Test-Path $log) {
            $readyLine = Get-Content -LiteralPath $log -Encoding UTF8 | Where-Object {
                $_ -match "Első főablak-képkocka; a rács megjelent|A főablak a splash után megjelent"
            } | Select-Object -Last 1
            if ($readyLine) {
                $timestamp = ($readyLine -split " INFO picasapy\.startup:", 2)[0]
                $readyAt = [DateTimeOffset]::Parse($timestamp)
                break
            }
        }
        if ($app.HasExited) { throw "a PicasaPy a főablak megjelenése előtt kilépett" }
        Start-Sleep -Milliseconds 50
    }
    if (-not $readyAt) { throw "120 másodpercen belül nem jelent meg az első főablak-képkocka" }
    $elsoIndulasMp = ($readyAt - $appStart).TotalSeconds
    Write-Output ("Telepítés utáni első indulás a főablakig: {0:N2} s" -f $elsoIndulasMp)
    if ($elsoIndulasMp -gt $script:_elso_indulas_hatar_mp) {
        throw "az első indulás lassabb a későbbi indulás $($script:_elso_indulas_hatar_mp) s-os határánál"
    }

    if (Test-Path $legacyExe) { throw "a régi felhasználói telepítés a frissítés után is megmaradt" }
    if (Get-CurrentUserUninstallEntry) { throw "a régi felhasználói eltávolítási bejegyzés megmaradt" }
} catch {
    Write-Host "Telepítőpróba hiba: $($_.Exception.ToString())"
    Save-FailureScreenshot
    throw
} finally {
    if ($app) {
        Stop-Process -Id $app.Id -Force -ErrorAction SilentlyContinue
        $app.Dispose()
    }
    if ($setup) { $setup.Dispose() }
}
