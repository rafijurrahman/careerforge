Output "demo/eligibility.gif"

Set Shell "powershell"
Set FontSize 15
Set Width 1050
Set Height 600
Set Theme "Catppuccin Mocha"
Set WindowBar Colorful
Set TypingSpeed 20ms

Hide
Type ". C:\demo\setup_env.ps1"
Enter
Sleep 1s
Show

Type "forge eligibility --jd examples/job_restricted.txt --my-country BD"
Sleep 300ms
Enter
Sleep 6s