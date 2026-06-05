# Source this in your PowerShell profile to enable Ctrl+G.
# Add to profile:
# . "$HOME\.config\ask\ask.ps1"

Set-PSReadLineKeyHandler -Chord 'Ctrl+g' -ScriptBlock {
    $line = $null
    $cursor = $null
    [Microsoft.PowerShell.PSConsoleReadLine]::GetBufferState([ref]$line, [ref]$cursor)
    if ([string]::IsNullOrWhiteSpace($line)) { return }

    $cmd = ask --raw $line 2>$null
    if ($LASTEXITCODE -eq 0 -and $cmd) {
        [Microsoft.PowerShell.PSConsoleReadLine]::ReplaceLine($cmd)
    }
}

