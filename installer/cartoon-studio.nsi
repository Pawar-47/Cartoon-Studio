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
ShowInstDetails show
ShowUnInstDetails show
VIProductVersion "${APP_VERSION}.0"
VIAddVersionKey "ProductName" "Cartoon Studio"
VIAddVersionKey "ProductVersion" "${APP_VERSION}"
VIAddVersionKey "FileVersion" "${APP_VERSION}"
VIAddVersionKey "FileDescription" "Cartoon Studio Installer"

Section "Cartoon Studio" SEC_MAIN
    SetShellVarContext current

    ; Stop an existing process before replacing its program files.
    ExecWait '"$SYSDIR\taskkill.exe" /F /IM CartoonStudio.exe'

    ; Run the previous uninstaller on upgrade. User data is outside $INSTDIR.
    IfFileExists "$INSTDIR\Uninstall.exe" 0 no_previous_install
        ExecWait '"$INSTDIR\Uninstall.exe" /S _?=$INSTDIR'
    no_previous_install:

    RMDir /r "$INSTDIR"
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
    WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\CartoonStudio" "NoModify" 1
    WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\CartoonStudio" "NoRepair" 1
SectionEnd

Section "Uninstall"
    SetShellVarContext current
    ExecWait '"$SYSDIR\taskkill.exe" /F /IM CartoonStudio.exe'

    Delete "$SMPROGRAMS\Cartoon Studio\Cartoon Studio.lnk"
    RMDir "$SMPROGRAMS\Cartoon Studio"
    Delete "$DESKTOP\Cartoon Studio.lnk"
    DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\CartoonStudio"
    DeleteRegKey HKCU "Software\CartoonStudio"
    LogText "Removing program directory: $INSTDIR"
    RMDir /r "$INSTDIR"

    ; Deliberately preserve %LOCALAPPDATA%\CartoonStudio and all project data.
SectionEnd

Function un.onInit
    SetShellVarContext current
    ReadRegStr $INSTDIR HKCU "Software\CartoonStudio" "InstallDir"
    LogSet on
    LogText "Uninstaller resolved install directory: $INSTDIR"
    StrCmp $INSTDIR "" set_default_install_dir done_init
set_default_install_dir:
    StrCpy $INSTDIR "$LOCALAPPDATA\Programs\Cartoon Studio"
done_init:
FunctionEnd
