; Inno Setup szkript a windowsos PicasaPy-telepítőhöz (#3021).
;
; A verziót KÍVÜLRŐL kapja, hogy egyetlen forrás legyen (a pyproject.toml):
;     iscc /DMyAppVersion=0.8.423 packaging\windows\picasapy.iss
;
; Bemenet: a PyInstaller kimenete (dist\PicasaPy\).
; Kimenet: packaging\dist\PicasaPy-Setup-<verzió>.exe

#ifndef MyAppVersion
  #error A verziot a build adja at: iscc /DMyAppVersion=x.y.z
#endif

#define MyAppName "PicasaPy"
#define MyAppExeName "PicasaPy.exe"

[Setup]
; Az AppId a telepítés KILÉTE: erre épül az „Alkalmazások és
; szolgáltatások" alatti bejegyzés és a frissítés felismerése. Ha
; megváltozik, egy frissítés MÁSODIK bejegyzést hagy — ezért állandó.
AppId={{9F3C1D28-7C4E-4E2B-9A55-3B1D6A0C77E1}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher=PicasaPy
AppPublisherURL=https://github.com/sanchomuzax/PicasaPy
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
; rendszergazdai jog nélkül is telepíthető legyen (felhasználói profilba)
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=..\dist
OutputBaseFilename=PicasaPy-Setup-{#MyAppVersion}
SetupIconFile=..\..\src\picasapy\app\assets\icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
; magyar felület, ha elérhető — a felhasználó anyanyelve
ShowLanguageDialog=no

[Languages]
Name: "hu"; MessagesFile: "compiler:Languages\Hungarian.isl"
Name: "en"; MessagesFile: "compiler:Default.isl"

[CustomMessages]
hu.RemoveOtherInstallation=Egy másik mappába telepített PicasaPy található itt: %1. Eltávolítja az új telepítés előtt?
en.RemoveOtherInstallation=A PicasaPy is installed in a different folder: %1. Remove it before installing this version?
hu.UninstallFailed=A régi PicasaPy eltávolítása nem sikerült: %1. Az új telepítés folytatódik; a régit később a Gépházban (Alkalmazások) távolíthatja el.
en.UninstallFailed=The old PicasaPy could not be uninstalled: %1. Setup will continue; you can remove the old one later in Settings (Apps).

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; \
    GroupDescription: "{cm:AdditionalIcons}"

[Files]
; a teljes PyInstaller-mappa, a Python futtatókörnyezettel együtt
Source: "..\..\dist\PicasaPy\*"; DestDir: "{app}"; \
    Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; #6345: a parancsikon UGYANAZT az AppUserModelID-t viseli, amit a program
; induláskor beállít (`application_platform._set_windows_app_id`, #67).
; Eltérő azonosítónál a Windows a futó ablakot és a parancsikont két külön
; alkalmazásnak látja: a tálcára rögzített ikon mellett külön, ikon nélküli
; gomb nyílik.
#define MyAppUserModelID "PicasaPy.PicasaPy"
; Start menü
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; \
    AppUserModelID: "{#MyAppUserModelID}"
; asztali ikon (a telepítő kérdezi)
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; \
    AppUserModelID: "{#MyAppUserModelID}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Parameters: "--qml-elofordit"; Flags: runhidden waituntilterminated runasoriginaluser
Filename: "{app}\{#MyAppExeName}"; Parameters: "--qml-grafika-melegites"; Flags: runhidden waituntilterminated runasoriginaluser
Filename: "{app}\{#MyAppExeName}"; \
    Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; \
    Flags: nowait postinstall skipifsilent

[Code]
const
  PicasaPyUninstallKey = 'Software\Microsoft\Windows\CurrentVersion\Uninstall\{9F3C1D28-7C4E-4E2B-9A55-3B1D6A0C77E1}_is1';
  SilentUninstallParameters = '/VERYSILENT /SUPPRESSMSGBOXES /NORESTART';

function SplitUninstallCommand(const CommandLine: String; var ExeName, Parameters: String): Boolean;
var
  Value: String;
  Boundary: Integer;
begin
  Result := False;
  ExeName := '';
  Parameters := '';
  Value := Trim(CommandLine);
  if Value = '' then
    Exit;

  if Value[1] = '"' then
  begin
    Delete(Value, 1, 1);
    Boundary := Pos('"', Value);
    if Boundary = 0 then
      Exit;
    ExeName := Copy(Value, 1, Boundary - 1);
    Parameters := Trim(Copy(Value, Boundary + 1, Length(Value)));
  end
  else
  begin
    Boundary := Pos('.exe', Lowercase(Value));
    if Boundary = 0 then
      Exit;
    ExeName := Copy(Value, 1, Boundary + 3);
    Parameters := Trim(Copy(Value, Boundary + 4, Length(Value)));
  end;

  Result := FileExists(ExeName);
end;

function SameInstallDirectory(const FirstPath, SecondPath: String): Boolean;
var
  FirstDirectory, SecondDirectory: String;
begin
  FirstDirectory := AddBackslash(ExpandFileName(FirstPath));
  SecondDirectory := AddBackslash(ExpandFileName(SecondPath));
  Result := CompareText(FirstDirectory, SecondDirectory) = 0;
end;

function RemoveDifferentInstallation(const RootKey: Integer): String;
var
  UninstallString, InstallLocation, ExeName, Parameters: String;
  ResultCode: Integer;
begin
  Result := '';
  if not RegQueryStringValue(RootKey, PicasaPyUninstallKey, 'UninstallString', UninstallString) then
    Exit;
  if not SplitUninstallCommand(UninstallString, ExeName, Parameters) then
    Exit;
  if not RegQueryStringValue(RootKey, PicasaPyUninstallKey, 'InstallLocation', InstallLocation) then
    InstallLocation := ExtractFileDir(ExeName);
  if InstallLocation = '' then
    InstallLocation := ExtractFileDir(ExeName);

  if SameInstallDirectory(InstallLocation, WizardDirValue) then
    Exit;

  if SuppressibleMsgBox(
       FmtMessage(CustomMessage('RemoveOtherInstallation'), [InstallLocation]),
       mbConfirmation, MB_YESNO, IDYES) <> IDYES then
    Exit;

  if Parameters <> '' then
    Parameters := Parameters + ' ';
  Parameters := Parameters + SilentUninstallParameters;
  { ShellExec: a rendszergazdai telepítés eltávolítója a manifestje szerint
    UAC-emelést kér; az Exec (CreateProcess) ilyenkor 740-es hibával elbukna. }
  if (not ShellExec('', ExeName, Parameters, '', SW_HIDE, ewWaitUntilTerminated, ResultCode))
     or (ResultCode <> 0) then
    { a sikertelen eltávolítás nem állítja meg az új telepítést: jelezzük,
      és a felhasználó később kézzel is eltávolíthatja a régit }
    SuppressibleMsgBox(FmtMessage(CustomMessage('UninstallFailed'), [InstallLocation]),
      mbError, MB_OK, IDOK);
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
begin
  Result := RemoveDifferentInstallation(HKEY_CURRENT_USER_32);
  if Result <> '' then
    Exit;
  if IsWin64 then
  begin
    Result := RemoveDifferentInstallation(HKEY_CURRENT_USER_64);
    if Result <> '' then
      Exit;
  end;

  Result := RemoveDifferentInstallation(HKEY_LOCAL_MACHINE_32);
  if Result <> '' then
    Exit;
  if IsWin64 then
    Result := RemoveDifferentInstallation(HKEY_LOCAL_MACHINE_64);
end;
