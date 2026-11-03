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
    public string Text;
    public string ClassName;
    public bool Visible;
    public bool Enabled;
    public int Width;
    public int Height;
}

public static class PicasaPyNative
{
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

    private static PicasaPyWindow Describe(IntPtr hwnd)
    {
        var text = new StringBuilder(512);
        var className = new StringBuilder(256);
        GetWindowTextW(hwnd, text, text.Capacity);
        GetClassNameW(hwnd, className, className.Capacity);
        RECT rect;
        GetWindowRect(hwnd, out rect);
        return new PicasaPyWindow {
            Handle = hwnd,
            Text = text.ToString(),
            ClassName = className.ToString(),
            Visible = IsWindowVisible(hwnd),
            Enabled = IsWindowEnabled(hwnd),
            Width = Math.Max(0, rect.Right - rect.Left),
            Height = Math.Max(0, rect.Bottom - rect.Top)
        };
    }

    public static PicasaPyWindow[] ForProcess(int targetPid)
    {
        var result = new List<PicasaPyWindow>();
        EnumWindows((top, _) => {
            uint pid;
            GetWindowThreadProcessId(top, out pid);
            if (pid != targetPid) return true;
            result.Add(Describe(top));
            EnumChildWindows(top, (child, __) => {
                uint childPid;
                GetWindowThreadProcessId(child, out childPid);
                if (childPid == targetPid) result.Add(Describe(child));
                return true;
            }, IntPtr.Zero);
            return true;
        }, IntPtr.Zero);
        return result.ToArray();
    }

    public static bool ClickPhysical(IntPtr hwnd)
    {
        RECT rect;
        if (!GetWindowRect(hwnd, out rect) || rect.Right <= rect.Left || rect.Bottom <= rect.Top)
            return false;
        if (!SetCursorPos((rect.Left + rect.Right) / 2, (rect.Top + rect.Bottom) / 2))
            return false;
        const uint inputMouse = 0;
        const uint leftDown = 0x0002;
        const uint leftUp = 0x0004;
        var inputs = new[] {
            new INPUT { type = inputMouse, mi = new MOUSEINPUT { dwFlags = leftDown } },
            new INPUT { type = inputMouse, mi = new MOUSEINPUT { dwFlags = leftUp } }
        };
        return SendInput((uint)inputs.Length, inputs, Marshal.SizeOf(typeof(INPUT))) == inputs.Length;
    }

}
'@

function Normalize-Caption([string]$Text) {
    return ($Text -replace "&", "").Trim()
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

$installer = (Resolve-Path $Installer).Path
$installDir = [IO.Path]::GetFullPath($InstallDir)
$legacyExe = [IO.Path]::GetFullPath($LegacyExe)
$executable = Join-Path $installDir "PicasaPy.exe"
$profile = Join-Path $env:RUNNER_TEMP "PicasaPy-first-click-profile"
$local = Join-Path $profile "AppData\Local"
$roaming = Join-Path $profile "AppData\Roaming"
$temporary = Join-Path $profile "Temp"
New-Item -ItemType Directory -Force -Path $local, $roaming, $temporary | Out-Null
$env:USERPROFILE = $profile
$env:LOCALAPPDATA = $local
$env:APPDATA = $roaming
$env:TEMP = $temporary
$env:TMP = $temporary
$env:PICASAPY_LANG = "en"
Remove-Item Env:QT_QPA_PLATFORM -ErrorAction SilentlyContinue
Remove-Item Env:QT_QUICK_BACKEND -ErrorAction SilentlyContinue

$setup = Start-Process -FilePath $installer -ArgumentList @(
    "/SP-", "/NORESTART", "/ALLUSERS", "/DIR=$installDir"
) -PassThru
$setupDeadline = [DateTimeOffset]::UtcNow.AddMinutes(12)
$finishClickedAt = $null

while ([DateTimeOffset]::UtcNow -lt $setupDeadline) {
    $setup.Refresh()
    if ($setup.HasExited) { throw "a telepítő a Befejezés előtt kilépett: $($setup.ExitCode)" }
    $windows = [PicasaPyNative]::ForProcess($setup.Id)
    $wizard = $windows | Where-Object { $_.ClassName -eq "TWizardForm" } | Select-Object -First 1
    if (-not $wizard) {
        Start-Sleep -Milliseconds 100
        continue
    }

    $captions = @($windows | ForEach-Object { Normalize-Caption $_.Text })
    if (($captions -join " ") -match "different folder|másik mappába telepített") {
        $yes = $windows | Where-Object {
            $_.Visible -and $_.Enabled -and (Normalize-Caption $_.Text) -match "^(Yes|Igen)$"
        } | Select-Object -First 1
        if (-not $yes -or -not [PicasaPyNative]::ClickPhysical($yes.Handle)) {
            throw "a korábbi felhasználói telepítés eltávolítását nem sikerült jóváhagyni"
        }
        Start-Sleep -Milliseconds 100
        continue
    }
    if (($captions -join " ") -match "could not be uninstalled|eltávolítása nem sikerült") {
        throw "a régi PicasaPy eltávolítása nem sikerült"
    }

    $buttons = @($windows | Where-Object {
        $_.Visible -and $_.Enabled -and $_.ClassName -match "Button"
    })
    $finish = $buttons | Where-Object {
        (Normalize-Caption $_.Text) -match "^(Finish|Befejezés)$"
    } | Select-Object -First 1
    if ($finish) {
        $finishClickedAt = [DateTimeOffset]::UtcNow
        if (-not [PicasaPyNative]::ClickPhysical($finish.Handle)) {
            throw "a telepítő Befejezés gombjára nem sikerült valódi egérkattintást küldeni"
        }
        break
    }

    $next = $buttons | Where-Object {
        (Normalize-Caption $_.Text) -match "^(Next|Tovább)\s*>?$"
    } | Select-Object -First 1
    if (-not $next) {
        $next = $buttons | Where-Object {
            (Normalize-Caption $_.Text) -match "^(Install|Telepítés)$"
        } | Select-Object -First 1
    }
    if ($next -and -not [PicasaPyNative]::ClickPhysical($next.Handle)) {
        throw "a telepítő következő oldalára nem sikerült egérkattintással továbblépni"
    }
    Start-Sleep -Milliseconds 100
}

if (-not $finishClickedAt) { throw "12 perc alatt nem jelent meg a Befejezés gomb" }
if (-not (Test-Path $executable)) { throw "a telepítés után hiányzik a PicasaPy.exe" }

$appDeadline = [DateTimeOffset]::UtcNow.AddSeconds(30)
$app = $null
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

try {
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

$setup.Refresh()
if (-not $setup.HasExited) { $setup.WaitForExit(10000) | Out-Null }
if (Test-Path $legacyExe) { throw "a régi felhasználói telepítés a frissítés után is megmaradt" }
if (Get-CurrentUserUninstallEntry) { throw "a régi felhasználói eltávolítási bejegyzés megmaradt" }
} finally {
    Stop-Process -Id $app.Id -Force -ErrorAction SilentlyContinue
    $app.Dispose()
}
