[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$failures = [System.Collections.Generic.List[string]]::new()
$warnings = [System.Collections.Generic.List[string]]::new()

function Pass([string]$message) { Write-Host "[PASS] $message" -ForegroundColor Green }
function Fail([string]$message) { $failures.Add($message); Write-Host "[FAIL] $message" -ForegroundColor Red }
function Warn([string]$message) { $warnings.Add($message); Write-Host "[WARN] $message" -ForegroundColor Yellow }

Write-Host "Devoteam Reference Data Pipeline preflight"
Write-Host "Repository: $repoRoot"

$python = Get-Command python -ErrorAction SilentlyContinue
if ($null -eq $python) {
    Fail 'Python is not available on PATH.'
} else {
    $versionOutput = & $python.Source -c "import sys; print('.'.join(map(str, sys.version_info[:3]))); raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" 2>&1
    if ($LASTEXITCODE -eq 0) { Pass "Python $versionOutput (>= 3.10)" } else { Fail "Python $versionOutput is older than 3.10." }

    $modules = @('yaml','googleapiclient','google.auth','fitz','PIL','pytesseract','numpy','pandas','pyarrow','openpyxl','docx','pptx','reportlab','pypdf','sentence_transformers','faiss','pytest')
    $moduleList = $modules -join ','
    $missingModules = & $python.Source -c "import importlib.util; mods='$moduleList'.split(','); print(','.join(m for m in mods if importlib.util.find_spec(m) is None))" 2>&1
    if ([string]::IsNullOrWhiteSpace($missingModules)) { Pass 'Canonical Python dependencies are importable.' } else { Fail "Missing Python modules: $missingModules" }
}

$tesseractCommand = Get-Command tesseract -ErrorAction SilentlyContinue
$tesseractPath = if ($null -ne $tesseractCommand) { $tesseractCommand.Source } else { Join-Path $env:ProgramFiles 'Tesseract-OCR\tesseract.exe' }
if (-not (Test-Path -LiteralPath $tesseractPath -PathType Leaf)) {
    Fail 'Tesseract OCR is not available on PATH.'
} else {
    $languages = @(& $tesseractPath --list-langs 2>&1)
    $missingLanguages = @('eng','fra','ara') | Where-Object { $_ -notin $languages }
    if ($missingLanguages.Count -eq 0) { Pass "Tesseract language packs eng, fra, and ara are available at $tesseractPath." } else { Fail "Missing Tesseract language packs: $($missingLanguages -join ', ')" }
}

$soffice = Get-Command soffice -ErrorAction SilentlyContinue
if ($null -eq $soffice) {
    $officeCandidates = @(@(
        (Join-Path $env:ProgramFiles 'LibreOffice\program\soffice.exe'),
        (Join-Path ${env:ProgramFiles(x86)} 'LibreOffice\program\soffice.exe')
    ) | Where-Object { -not [string]::IsNullOrWhiteSpace($_) -and (Test-Path -LiteralPath $_ -PathType Leaf) })
    if ($officeCandidates.Count -eq 0) { Fail 'LibreOffice soffice is not available.' } else { Pass "LibreOffice found at $($officeCandidates[0])." }
} else {
    Pass "LibreOffice found at $($soffice.Source)."
}

$requiredConfigs = @(
    'config\project.yaml',
    'config\security.yaml',
    'config\phase2_source.yaml',
    'config\phase3_extraction.yaml',
    'config\phase3_1_repair.yaml',
    'config\phase4_corpus.yaml',
    'config\phase5_retrieval.yaml'
)
foreach ($relative in $requiredConfigs) {
    $path = Join-Path $repoRoot $relative
    if (Test-Path -LiteralPath $path -PathType Leaf) { Pass "Configuration: $relative" } else { Fail "Missing configuration: $relative" }
}

$snapshotId = '20260714T154731Z_129ff982c8'
$rawRoot = Join-Path $repoRoot "data\snapshots\$snapshotId\raw"
if (Test-Path -LiteralPath $rawRoot -PathType Container) {
    Pass "Private raw snapshot directory is present: $snapshotId"
    if ($null -ne $python) {
        $previousPythonPath = $env:PYTHONPATH
        $env:PYTHONPATH = Join-Path $repoRoot 'src'
        $oldErrorAction = $ErrorActionPreference
        $ErrorActionPreference = 'Continue'
        & $python.Source (Join-Path $repoRoot 'scripts\validate_phase2.py') --project-root $repoRoot --snapshot (Join-Path $repoRoot "data\snapshots\$snapshotId") 2>$null | Out-Null
        $snapshotExit = $LASTEXITCODE
        $ErrorActionPreference = $oldErrorAction
        $env:PYTHONPATH = $previousPythonPath
        if ($snapshotExit -eq 0) { Pass 'Signed snapshot hashes and file inventory are complete.' } else { Fail 'Signed snapshot verification failed; restore missing or changed private source files.' }
    }
} else {
    Fail "Private raw snapshot is missing: $rawRoot"
}

$canonicalFiles = @(
    "data\canonical\$snapshotId\phase4_corpus_v1\canonical_pages.parquet",
    "data\canonical\$snapshotId\phase4_corpus_v1\chunks.parquet",
    "data\canonical\$snapshotId\phase4_corpus_v1\reference_catalog.parquet",
    "data\canonical\$snapshotId\phase4_corpus_v1\documents_catalog.parquet",
    "data\canonical\$snapshotId\phase4_corpus_v1\PHASE_4_MANIFEST.json",
    "data\canonical\$snapshotId\phase4_corpus_v1\SHA256SUMS.txt",
    "data\canonical\$snapshotId\phase4_corpus_v1\_SUCCESS.json",
    "data\indexes\$snapshotId\phase5_hybrid_retrieval_v1\bm25_index.npz",
    "data\indexes\$snapshotId\phase5_hybrid_retrieval_v1\bm25_vocabulary.json",
    "data\indexes\$snapshotId\phase5_hybrid_retrieval_v1\embeddings.npy",
    "data\indexes\$snapshotId\phase5_hybrid_retrieval_v1\chunk_lookup.parquet",
    "data\indexes\$snapshotId\phase5_hybrid_retrieval_v1\PHASE_5_MANIFEST.json",
    "data\indexes\$snapshotId\phase5_hybrid_retrieval_v1\_SUCCESS.json"
)
foreach ($relative in $canonicalFiles) {
    if (-not (Test-Path -LiteralPath (Join-Path $repoRoot $relative) -PathType Leaf)) { Fail "Missing canonical artifact: $relative" }
}
if ($failures.Count -eq 0) { Pass 'Canonical corpus and retrieval artifacts are present.' }

if ([string]::IsNullOrWhiteSpace($env:DEVOTEAM_SOURCE_SHORTCUT_ID) -or $env:DEVOTEAM_SOURCE_SHORTCUT_ID -like 'replace-*') {
    Warn 'DEVOTEAM_SOURCE_SHORTCUT_ID is not exported; Phase 2 ingestion is not ready.'
} else {
    Pass 'DEVOTEAM_SOURCE_SHORTCUT_ID is configured.'
}

Write-Host ''
Write-Host "Warnings: $($warnings.Count)"
Write-Host "Failures: $($failures.Count)"
if ($failures.Count -gt 0) {
    Write-Host 'PREFLIGHT_NOT_READY' -ForegroundColor Red
    exit 1
}
Write-Host 'PREFLIGHT_READY' -ForegroundColor Green
exit 0
