$edge='C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
if (-not (Test-Path $edge)) { $edge='C:\Program Files\Microsoft\Edge\Application\msedge.exe' }
& $edge --headless --disable-gpu --print-to-pdf="\\wsl.localhost\Ubuntu-22.04\root\alz-memory-assistant\docs\adventurex\ADVENTUREX_PROJECT_PROPOSAL_CN.pdf" "file:///\\wsl.localhost\Ubuntu-22.04\root\alz-memory-assistant\docs\adventurex\ADVENTUREX_PROJECT_PROPOSAL_CN.html"
& $edge --headless --disable-gpu --print-to-pdf="\\wsl.localhost\Ubuntu-22.04\root\alz-memory-assistant\docs\adventurex\ADVENTUREX_ONE_PAGE_CN.pdf" "file:///\\wsl.localhost\Ubuntu-22.04\root\alz-memory-assistant\docs\adventurex\ADVENTUREX_ONE_PAGE_CN.html"
& $edge --headless --disable-gpu --print-to-pdf="\\wsl.localhost\Ubuntu-22.04\root\alz-memory-assistant\docs\adventurex\ADVENTUREX_ONE_PAGE_EN.pdf" "file:///\\wsl.localhost\Ubuntu-22.04\root\alz-memory-assistant\docs\adventurex\ADVENTUREX_ONE_PAGE_EN.html"
