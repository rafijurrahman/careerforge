# CareerForge Terminal Demo: Remote Geo-Eligibility & Match (vhs)
# To render: vhs demo/eligibility.tape

Output demo/eligibility.gif

Set Shell "bash"
Set FontSize 18
Set Width 1200
Set Height 720
Set Theme "Catppuccin Mocha"
Set WindowBar Colorful
Set Margin 20

Type "forge match --jd examples/sample_jd.txt --profile examples/profile.example.yaml --my-country BD"
Sleep 500ms
Enter
Sleep 4s

Type "forge eligibility --jd 'Remote anywhere! Candidates must reside in the US and not require visa sponsorship.' --my-country BD"
Sleep 500ms
Enter
Sleep 4s
