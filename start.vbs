Set WshShell = CreateObject("WScript.Shell")
Set FSO = CreateObject("Scripting.FileSystemObject")
repoPath = FSO.GetParentFolderName(WScript.ScriptFullName)
cmd = "cmd /c cd /d """ & repoPath & """ && uv run window-transcribe-shortcut"
WshShell.Run cmd, 0, False
