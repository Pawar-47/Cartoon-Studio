Unicode true
RequestExecutionLevel user
SetCompressor /SOLID zlib

!ifndef APP_VERSION
!define APP_VERSION "0.1.0"
!endif
!ifndef APP_DIST_DIR
!define APP_DIST_DIR "dist\v2\CartoonStudio"
!endif
!ifndef OUTPUT_FILE
!define OUTPUT_FILE "dist\Cartoon-Studio-Setup.exe"
!endif

Name "Cartoon Studio"
OutFile "${OUTPUT_FILE}"
InstallDir "$LOCALAPPDATA\Programs\Cartoon Studio"
InstallDirRegKey HKCU "Software\CartoonStudio" "InstallDir"
Page instfiles
ShowInstDetails show
ShowUnInstDetails show
UninstPage uninstConfirm
UninstPage instfiles
VIProductVersion "${APP_VERSION}.0"
VIAddVersionKey "ProductName" "Cartoon Studio"
VIAddVersionKey "ProductVersion" "${APP_VERSION}"
VIAddVersionKey "FileVersion" "${APP_VERSION}"
VIAddVersionKey "FileDescription" "Cartoon Studio Installer"

!macro RemoveInstalledFiles
    ; Remove only known application-owned paths. Never touch the user's data directory.
    SetOutPath "$TEMP"
    SetFileAttributes "$INSTDIR\CartoonStudio.exe" NORMAL
    SetFileAttributes "$INSTDIR\dependency-sbom.cdx.json" NORMAL
    SetFileAttributes "$INSTDIR\THIRD_PARTY_NOTICES.md" NORMAL
    RMDir /r "$INSTDIR\_internal"
    RMDir /r "$INSTDIR\LICENSES"
    Delete "$INSTDIR\CartoonStudio.exe"
    Delete "$INSTDIR\dependency-sbom.cdx.json"
    Delete "$INSTDIR\THIRD_PARTY_NOTICES.md"
!macroend

Section "Cartoon Studio" SEC_MAIN
    SectionIn RO
    SetShellVarContext current
    SetRegView 64

    ; Stop an existing app before replacing program files. Do not invoke the
    ; previous uninstaller during upgrades: it can remove install metadata and
    ; shortcuts while this installer is still running.
    ExecWait '"$SYSDIR\taskkill.exe" /F /IM CartoonStudio.exe'

    !insertmacro RemoveInstalledFiles
    CreateDirectory "$INSTDIR"
    SetOutPath "$INSTDIR"
    File /r "${APP_DIST_DIR}\*"

    WriteUninstaller "$INSTDIR\Uninstall.exe"

    CreateDirectory "$SMPROGRAMS\Cartoon Studio"
    CreateShortCut "$SMPROGRAMS\Cartoon Studio\Cartoon Studio.lnk" "$INSTDIR\CartoonStudio.exe"
    CreateShortCut "$DESKTOP\Cartoon Studio.lnk" "$INSTDIR\CartoonStudio.exe"

    WriteRegStr HKCU "Software\CartoonStudio" "InstallDir" "$INSTDIR"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\CartoonStudio" "DisplayName" "Cartoon Studio"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\CartoonStudio" "DisplayVersion" "${APP_VERSION}"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\CartoonStudio" "InstallLocation" "$INSTDIR"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\CartoonStudio" "UninstallString" '"$INSTDIR\Uninstall.exe"'
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\CartoonStudio" "QuietUninstallString" '"$INSTDIR\Uninstall.exe" /S'
    WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\CartoonStudio" "NoModify" 1
    WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\CartoonStudio" "NoRepair" 1
SectionEnd

Function un.onInit
    ; NSIS normally runs a temporary copy of the uninstaller. Restore the real
    ; application directory from the per-user registry before touching files.
    SetRegView 64
    WriteRegStr HKCU "Software\CartoonStudioDebug" "UnInitEntered" "yes"
    ReadRegStr $INSTDIR HKCU "Software\CartoonStudio" "InstallDir"
    WriteRegStr HKCU "Software\CartoonStudioDebug" "UnInitInstallDir" "$INSTDIR"
    IfFileExists "$INSTDIR\CartoonStudio.exe" un_install_path_valid
        SetErrorLevel 2
        Abort
    un_install_path_valid:
FunctionEnd

Section "Uninstall"
    SetShellVarContext current
    SetRegView 64
    WriteRegStr HKCU "Software\CartoonStudioDebug" "UninstallSectionEntered" "yes"
    WriteRegStr HKCU "Software\CartoonStudioDebug" "UninstallSectionInstallDir" "$INSTDIR"
    ExecWait '"$SYSDIR\taskkill.exe" /F /IM CartoonStudio.exe'

    Delete "$SMPROGRAMS\Cartoon Studio\Cartoon Studio.lnk"
    RMDir "$SMPROGRAMS\Cartoon Studio"
    Delete "$DESKTOP\Cartoon Studio.lnk"
    DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\CartoonStudio"
    DeleteRegKey HKCU "Software\CartoonStudio"

    !insertmacro RemoveInstalledFiles
    Delete "$INSTDIR\Uninstall.exe"
    RMDir "$INSTDIR"

    ; Deliberately preserve %LOCALAPPDATA%\CartoonStudio and all project data.
SectionEnd
