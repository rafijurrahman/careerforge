Output "demo/track.gif"

Set Shell "powershell"
Set FontSize 14
Set Width 1100
Set Height 850
Set Theme "Catppuccin Mocha"
Set WindowBar Colorful
Set TypingSpeed 20ms

Hide
Type ". C:\demo\setup_env.ps1"
Enter
Sleep 1s
Show

Type "forge track list"
Sleep 300ms
Enter
Sleep 3s

Type "forge ghost --top 3"
Sleep 300ms
Enter
Sleep 3s

Type "forge report"
Sleep 300ms
Enter
Sleep 5s