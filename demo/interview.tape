# CareerForge Terminal Demo: Honest STAR Interview Prep & Cover Drafts (vhs)
# To render: vhs demo/interview.tape

Output demo/interview.gif

Set Shell "bash"
Set FontSize 18
Set Width 1200
Set Height 720
Set Theme "Catppuccin Mocha"
Set WindowBar Colorful
Set Margin 20

Type "forge interview draft --profile examples/profile.example.yaml --limit 2"
Sleep 500ms
Enter
Sleep 4s

Type "forge interview practice --role backend --seed 42 --timer 90"
Sleep 500ms
Enter
Sleep 4s

Type "forge cover --jd examples/sample_jd.txt --profile examples/profile.example.yaml --type cold-email"
Sleep 500ms
Enter
Sleep 4s
