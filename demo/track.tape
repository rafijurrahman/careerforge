# CareerForge Terminal Demo: Local SQLite Tracker & Funnel Report (vhs)
# To render: vhs demo/track.tape

Output demo/track.gif

Set Shell "bash"
Set FontSize 18
Set Width 1200
Set Height 720
Set Theme "Catppuccin Mocha"
Set WindowBar Colorful
Set Margin 20

Type "export CAREERFORGE_DB=/tmp/careerforge_demo.db"
Sleep 300ms
Enter
Sleep 1s

Type "python examples/seed_demo_db.py --db $CAREERFORGE_DB"
Sleep 300ms
Enter
Sleep 2s

Type "forge track list"
Sleep 400ms
Enter
Sleep 3s

Type "forge report"
Sleep 400ms
Enter
Sleep 4s

Type "forge ghost --top 5"
Sleep 400ms
Enter
Sleep 3s
