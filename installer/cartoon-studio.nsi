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
InstallDir "$LocalAppData\Programs\Cartoon Studio"
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
    ; Never recursively delete the user's selected install root. Remove only known app-owned paths.
    SetOutPath "$TEMP"
    WriteRegStr HKCU "Software\CartoonStudioDebug" "Step1" "$INSTDIR"
    SetFileAttributes "$INSTDIR\CartoonStudio.exe" NORMAL
    SetFileAttributes "$INSTDIR\dependency-sbom.cdx.json" NORMAL
    SetFileAttributes "$INSTDIR\THIRD_PARTY_NOTICES.md" NORMAL
    RMDir /r "$INSTDIR\_internal"
    WriteRegStr HKCU "Software\CartoonStudioDebug" "Step2" "Internal removed"
    RMDir /r "$INSTDIR\LICENSES"
    WriteRegStr HKCU "Software\CartoonStudioDebug" "Step3" "Licenses removed"
    Delete "$INSTDIR\CartoonStudio.exe"
    WriteRegStr HKCU "Software\CartoonStudioDebug" "Step4" "Executable delete attempted"
    IfFileExists "$INSTDIR\CartoonStudio.exe" 0 +2
    WriteRegStr HKCU "Software\CartoonStudioDebug" "ExeStillExistsAfterDelete" "yes"
    Delete "$INSTDIR\dependency-sbom.cdx.json"
    Delete "$INSTDIR\THIRD_PARTY_NOTICES.md"
    WriteRegStr HKCU "Software\CartoonStudioDebug" "Step5" "App files removed"
!macroend

Section "Cartoon Studio" SEC_MAIN
    SectionIn RO
    WriteRegStr HKCU "Software\CartoonStudioDebug" "InstallSectionEntered" "yes"
    WriteRegStr HKCU "Software\CartoonStudioDebug" "InstallSectionPath" "$INSTDIR"
    SetShellVarContext current

    ; Stop an existing process before replacing its program files.
    ExecWait '"$SYSDIR\taskkill.exe" /F /IM CartoonStudio.exe'

    ; Run the previous uninstaller on upgrade. User data is outside $INSTDIR.
    IfFileExists "$INSTDIR\Uninstall.exe" 0 no_previous_install
        ExecWait '"$INSTDIR\Uninstall.exe" /S'
    no_previous_install:

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
    WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\CartoonStudio" "NoModify" 1
    WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\CartoonStudio" "NoRepair" 1
SectionEnd

Section "Uninstall"
    SetShellVarContext current
    SetRegView 64
    WriteRegStr HKCU "Software\CartoonStudioDebug" "SectionEntered" "yes"
    ExecWait '"$SYSDIR\taskkill.exe" /F /IM CartoonStudio.exe'

    Delete "$SMPROGRAMS\Cartoon Studio\Cartoon Studio.lnk"
    RMDir "$SMPROGRAMS\Cartoon Studio"
    Delete "$DESKTOP\Cartoon Studio.lnk"
    DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\CartoonStudio"
    DeleteRegKey HKCU "Software\CartoonStudio"
    IfErrors reg_delete_failed reg_delete_succeeded
reg_delete_failed:
    WriteRegStr HKCU "Software\CartoonStudioDebug" "RegDeleteResult" "error"
    Goto reg_delete_done
reg_delete_succeeded:
    WriteRegStr HKCU "Software\CartoonStudioDebug" "RegDeleteResult" "success"
reg_delete_done:
    ReadRegStr $1 HKCU "Software\CartoonStudio" "InstallDir"
    WriteRegStr HKCU "Software\CartoonStudioDebug" "RegistryAfterDelete" "$1"
    !insertmacro RemoveInstalledFiles
    IfFileExists "$INSTDIR\CartoonStudio.exe" exe_still_exists exe_removed
exe_still_exists:
    WriteRegStr HKCU "Software\CartoonStudioDebug" "ExeAfterCleanup" "exists"
    Goto exe_check_done
exe_removed:
    WriteRegStr HKCU "Software\CartoonStudioDebug" "ExeAfterCleanup" "gone"
exe_check_done:
    Delete "$INSTDIR\Uninstall.exe"
    RMDir "$INSTDIR"

    ; Deliberately preserve %LOCALAPPDATA%\CartoonStudio and all project data.
SectionEnd
