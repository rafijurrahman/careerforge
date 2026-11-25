Output "demo/hero.gif"

Set Shell "powershell"
Set FontSize 14
Set Width 1100
Set Height 800
Set Theme "Catppuccin Mocha"
Set WindowBar Colorful
Set TypingSpeed 20ms

Hide
Type ". C:\demo\setup_env.ps1"
Enter
Sleep 1s
Show

Type "forge tailor --jd examples/job_backend.txt"
Sleep 300ms
Enter
Sleep 14s

Type "forge ats-sim output/tailored/Alex_Rivera_Tailored_CV.pdf --profile examples/profile.example.yaml"
Sleep 500ms
Enter
Sleep 11s