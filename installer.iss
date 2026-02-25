; Inno Setup Script for DadoBounce
; Download Inno Setup from: https://jrsoftware.org/isinfo.php

#define MyAppName "DadoBounce"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "aimao0830"
#define MyAppURL "https://github.com/aimao0830/dadobounce"
#define MyAppExeName "dadobounce.exe"

[Setup]
AppId={{1DF85C1E-E64D-44D9-97F9-A4A720310B24}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
VersionInfoDescription={#MyAppName}
VersionInfoProductName={#MyAppName}
DefaultDirName={localappdata}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputDir=installer_output
OutputBaseFilename=DadoBounce_Setup_{#MyAppVersion}
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "chinesetraditional"; MessagesFile: "compiler:Languages\ChineseTraditional.isl"
Name: "chinesesimplified"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"

[CustomMessages]
english.OptionsGroup=Options:
english.AutostartOption=Start at Windows logon
chinesesimplified.OptionsGroup=选项:
chinesesimplified.AutostartOption=开机时自动启动
chinesetraditional.OptionsGroup=選項:
chinesetraditional.AutostartOption=開機時自動啟動

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "autostart"; Description: "{cm:AutostartOption}"; GroupDescription: "{cm:OptionsGroup}"

[Files]
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userstartup}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: autostart

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: dirifempty; Name: "{app}"

[Code]
function PrepareToInstall(var NeedsRestart: Boolean): String;
var
  ResultCode: Integer;
begin
  // Kill running instance before installing (so the exe can be overwritten)
  Exec('taskkill', '/F /IM {#MyAppExeName}', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  Result := '';
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  ResultCode: Integer;
  StartupShortcut: String;
begin
  if CurUninstallStep = usUninstall then
  begin
    // Kill running instance before uninstall
    Exec('taskkill', '/F /IM {#MyAppExeName}', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
    // Remove startup shortcut if it exists
    StartupShortcut := ExpandConstant('{userstartup}\DadoBounce.lnk');
    if FileExists(StartupShortcut) then
      DeleteFile(StartupShortcut);
  end;
end;
