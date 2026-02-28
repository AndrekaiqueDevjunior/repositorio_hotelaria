$file = 'g:\app_hotel_cabo_frio\frontend\app\(dashboard)\reservas\page.js'
$content = Get-Content $file -Raw

# Corrigir linha 1536: )} deve ser }) seguido de )
$content = $content -replace '(?m)^                \)\}\r?\n', "                })`n                )`n"

Set-Content $file -Value $content -NoNewline
Write-Host "Correcao aplicada com sucesso!"
