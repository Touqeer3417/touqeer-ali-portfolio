# Runs the unchanged RAGAS evaluation once per RRF_LIMIT value, then compares the reports.
# Usage (from D:\touqeer-ali-portfolio\backend, with .venv-eval active):
#   .\run_topk_sweep.ps1                 # K = 5, 4, 3
#   .\run_topk_sweep.ps1 -Limits 5,3
# Takes roughly 10 minutes per value. Nothing in app/ or evaluation/ is changed:
# RRF_LIMIT is the existing setting, passed only for the duration of each run.
param([int[]]$Limits = @(5, 4, 3))

if (-not (Test-Path ".\evaluation\evaluator.py")) {
    Write-Error "Run this from the backend folder (D:\touqeer-ali-portfolio\backend)."
    exit 1
}

try {
    foreach ($k in $Limits) {
        Write-Host "=== RRF_LIMIT=$k : evaluation started $(Get-Date -Format HH:mm:ss) ==="
        $env:RRF_LIMIT = "$k"
        python -m evaluation.evaluator --warmup 2> "eval_k$k.log"
        Write-Host "=== RRF_LIMIT=$k : finished $(Get-Date -Format HH:mm:ss) ==="
    }
}
finally {
    Remove-Item Env:RRF_LIMIT -ErrorAction SilentlyContinue
}

python compare_reports.py --last $Limits.Count
