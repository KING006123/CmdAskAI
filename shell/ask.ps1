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
        # 捕获的多行输出会是数组,合并成单个字符串并去掉首尾空白
        $cmd = (($cmd -join "`n").Trim())
        if ($cmd) {
            # PSConsoleReadLine 没有 ReplaceLine,用 Replace(start, length, text) 替换整行
            [Microsoft.PowerShell.PSConsoleReadLine]::Replace(0, $line.Length, $cmd)
        }
    }
}
