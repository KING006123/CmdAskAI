# Source this in your PowerShell profile to enable Ctrl+G.
# Add to profile:
# . "$env:APPDATA\ask\ask.ps1"

Set-PSReadLineKeyHandler -Chord 'Ctrl+g' -ScriptBlock {
    $line = $null
    $cursor = $null
    [Microsoft.PowerShell.PSConsoleReadLine]::GetBufferState([ref]$line, [ref]$cursor)
    if ([string]::IsNullOrWhiteSpace($line)) { return }

    $cmd = ask --raw --stream $line
    if ($LASTEXITCODE -eq 0 -and $cmd) {
        [Microsoft.PowerShell.PSConsoleReadLine]::ReplaceLine($cmd)
    }
}
