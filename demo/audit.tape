Output "demo/audit.gif"

Set Shell "powershell"
Set FontSize 12
Set Width 1100
Set Height 920
Set Theme "Catppuccin Mocha"
Set WindowBar Colorful
Set TypingSpeed 20ms

Hide
Type ". C:\demo\setup_env.ps1"
Enter
Sleep 1s
Show

Type "forge audit --file examples/sample_ai_text.txt"
Sleep 300ms
Enter
Sleep 6s