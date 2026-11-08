$ErrorActionPreference='Stop'
$PSNativeCommandUseErrorActionPreference=$false
$taskDir=$PSScriptRoot
$taskExpected=Get-Content -LiteralPath (Join-Path $taskDir 'expected.json') -Raw | ConvertFrom-Json
$taskRows=@($taskExpected.scores)
if($taskRows.Count -ne 2 -or @($taskRows.id | Sort-Object -Unique).Count -ne 2){throw 'Unexpected score set.'}
foreach($s in $taskRows){if($s.sessionId -cne 'c3-minisql/codex/20261108T150341Z-463d8062' -or $s.metadata.scope_id -cne $taskExpected.scope){throw 'Session or scope mismatch.'}}
. 'C:/Users/gerald.khoo/AppData/Local/Temp/claude/3003f0218900c270/1053a692-60d1-4fbf-a2f1-ab50d9c292fd/scratchpad/c3tools/lfenv.ps1'
$env:LANGFUSE_PUBLIC_KEY=$env:LANGFUSE_CODEX_PUBLIC_KEY;$env:LANGFUSE_SECRET_KEY=$env:LANGFUSE_CODEX_SECRET_KEY
$env:LANGFUSE_BASE_URL=$env:LANGFUSE_CODEX_BASE_URL;$env:LANGFUSE_HOST=$env:LANGFUSE_BASE_URL
$u=[Uri]$env:LANGFUSE_BASE_URL
if($u.Scheme -ne 'https' -or $u.Host -ne 'langfuse.markefin.com' -or $u.UserInfo -or $u.Query -or $u.Fragment){throw 'Unexpected Langfuse endpoint.'}
$configsRaw=& langfuse api score-configs list --all --json 2>&1
if($LASTEXITCODE){throw 'Score configuration read failed.'}
$configs=@(($configsRaw|Out-String|ConvertFrom-Json).body.data | Where-Object {$_.id -ceq 'fe4ba7b1-73e6-4807-96bc-588fa7b2d25a' -and $_.name -ceq 'oracle_pass_rate' -and $_.dataType -ceq 'NUMERIC' -and $_.minValue -eq 0 -and $_.maxValue -eq 1 -and -not $_.isArchived})
if($configs.Count -ne 1){throw 'Expected oracle score configuration is absent or incompatible.'}
$ids=($taskRows.id -join ',')
$before=& langfuse api scores list --id $ids --fields 'details,subject' --all --max-items 100 --json 2>&1
if($LASTEXITCODE){throw 'Score preflight read failed; nothing published.'}
$beforeDoc=$before|Out-String|ConvertFrom-Json
if(@($beforeDoc.body.data).Count -ne 0 -or $beforeDoc.body.meta.truncated){throw 'Scoped score ID already exists or preflight incomplete; nothing published.'}
[IO.File]::WriteAllText((Join-Path $taskDir 'preflight.json'),($before|Out-String),[Text.UTF8Encoding]::new($false))
$claim=[ordered]@{utc=[DateTime]::UtcNow.ToString('o');state='claimed-before-publication';scope=$taskExpected.scope;ids=@($taskRows.id);expected_sha256=(Get-FileHash (Join-Path $taskDir 'expected.json') -Algorithm SHA256).Hash.ToLowerInvariant()}
$stream=[IO.File]::Open((Join-Path $taskDir 'publication.claim.json'),[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
try{$bytes=[Text.Encoding]::UTF8.GetBytes(($claim|ConvertTo-Json -Depth 8));$stream.Write($bytes,0,$bytes.Length);$stream.Flush($true)}finally{$stream.Dispose()}
foreach($s in $taskRows){
 $file=Join-Path $taskDir ($s.name+'.json')
 $posted=& langfuse api scores create --body-file $file --json 2>&1
 $code=$LASTEXITCODE
 [IO.File]::WriteAllText((Join-Path $taskDir ($s.name+'.post.json')),($posted|Out-String),[Text.UTF8Encoding]::new($false))
 if($code -ne 0){throw "Score publication returned nonzero for $($s.name); inspect readback before any retry."}
}
$matches=$false
for($attempt=0;$attempt -lt 10 -and -not $matches;$attempt++){
 if($attempt -gt 0){Start-Sleep -Seconds 3}
 $raw=& langfuse api scores list --id $ids --fields 'details,subject' --all --max-items 100 --json 2>&1
 if($LASTEXITCODE){throw 'Readback failed after publication; inspect state before retry.'}
 $doc=$raw|Out-String|ConvertFrom-Json
 $found=@($doc.body.data)
 if($found.Count -ne 2 -or $doc.body.meta.truncated){continue}
 $matches=$true
 foreach($wanted in $taskRows){
  $hits=@($found|Where-Object {$_.id -ceq $wanted.id})
  if($hits.Count -ne 1){$matches=$false;break}
  $x=$hits[0]
  if($x.name -cne $wanted.name -or $x.dataType -cne 'NUMERIC' -or [math]::Abs([double]$x.value-[double]$wanted.value) -gt 0.00000001 -or $x.subject.kind -cne 'session' -or $x.subject.id -cne $wanted.sessionId -or $x.metadata.scope_id -cne $wanted.metadata.scope_id -or $x.metadata.quality_evidence_sha256 -cne $wanted.metadata.quality_evidence_sha256 -or $x.comment -cne $wanted.comment){$matches=$false;break}
  if($wanted.configId -and $x.configId -cne $wanted.configId){$matches=$false;break}
 }
}
if(-not $matches){throw 'Exact readback not established; inspect before any retry.'}
[IO.File]::WriteAllText((Join-Path $taskDir 'readback.json'),($raw|Out-String),[Text.UTF8Encoding]::new($false))
[ordered]@{status='verified';utc=[DateTime]::UtcNow.ToString('o');scope=$taskExpected.scope;ids=@($taskRows.id);count=2;historic_ids_touched=$false} | ConvertTo-Json | Set-Content (Join-Path $taskDir 'publication-result.json') -Encoding utf8
Write-Output 'Two scoped C3 metrics verified by Scores v3 readback.'

