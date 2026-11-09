; Inno Setup Script for Arooj Cloth and Bedsheet Parda Desktop POS
; Packages the PyInstaller distribution into a professional Windows Installer: Arooj_POS_Setup.exe

#define MyAppName "Arooj Cloth and Bedsheet Parda POS"
#define MyAppVersion "2.0.0"
#define MyAppPublisher "Arooj Home Textiles"
#define MyAppExeName "Arooj_POS_v2.exe"

[Setup]
AppId={{C6418B57-E9A0-449A-99B7-23B68A57A901}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\AroojPOS_v2
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputDir=..\dist
OutputBaseFilename=Arooj_POS_v2_Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
DisableProgramGroupPage=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Dist directory containing PyInstaller folder output
Source: "..\dist\Arooj_POS_v2\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; NOTE: Do NOT delete {localappdata}\AroojPOS_v2 to guarantee that shop database, backups, and settings survive uninstalls/upgrades!
Type: filesandordirs; Name: "{app}"
