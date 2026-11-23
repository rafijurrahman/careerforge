# CareerForge Terminal Demo Tape (vhs)
# To render: vhs demo/demo.tape

Output demo/demo.gif

Set Shell "bash"
Set FontSize 18
Set Width 1200
Set Height 720
Set Theme "Catppuccin Mocha"
Set WindowBar Colorful
Set Margin 20

Type "forge doctor"
Sleep 500ms
Enter
Sleep 3s

Type "forge audit --file examples/sample_ai_text.txt"
Sleep 500ms
Enter
Sleep 4s

Type "forge apply --profile examples/profile.example.yaml"
Sleep 500ms
Enter
Sleep 4s

Type "# 1-Page ATS CV generated offline!"
Sleep 2s
