# CareerForge Terminal Demo: ATS Parser Fragility Checker (vhs)
# To render: vhs demo/ats_sim.tape

Output demo/ats_sim.gif

Set Shell "bash"
Set FontSize 18
Set Width 1200
Set Height 720
Set Theme "Catppuccin Mocha"
Set WindowBar Colorful
Set Margin 20

Type "forge ats-sim examples/sample_output/Alex_Rivera_Universal_CV.pdf --profile examples/profile.example.yaml"
Sleep 500ms
Enter
Sleep 5s

Type "# Offline parser fragility check complete (heuristic, not a real ATS)."
Sleep 2s
