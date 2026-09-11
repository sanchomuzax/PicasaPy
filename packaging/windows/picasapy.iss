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

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; \
    GroupDescription: "{cm:AdditionalIcons}"

[Files]
; a teljes PyInstaller-mappa, a Python futtatókörnyezettel együtt
Source: "..\..\dist\PicasaPy\*"; DestDir: "{app}"; \
    Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Start menü
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
; asztali ikon (a telepítő kérdezi)
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; \
    Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; \
    Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; \
    Flags: nowait postinstall skipifsilent
