param(
    [switch]$KeepContainers
)

$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$runSuffix = "$PID"
$network = "hotel_waf_test_network_${runSuffix}"
$backend = "hotel_waf_test_backend_${runSuffix}"
$waf = "hotel_waf_test_proxy_${runSuffix}"
$image = "owasp/modsecurity-crs:4.28.0-nginx-202607100407@sha256:caa33403214c6898c68b78707a729674bf718ef834ea7834433a30dbc6b17b26"
$httpPort = $null
$httpsPort = $null

$productionCompose = [System.IO.File]::ReadAllText(
    (Join-Path $root "docker-compose.production.yml")
)
if ($productionCompose -match '--access-logfile|--access-logformat') {
    throw "Access log Uvicorn/Gunicorn pode vazar path ou query string"
}
Write-Host "[OK] access log inseguro do backend esta desativado"

function Remove-TestResources {
    foreach ($name in @($waf, $backend)) {
        $containerId = docker ps --all --quiet --filter "name=^/${name}$"
        if ($containerId) {
            docker rm --force $containerId | Out-Null
        }
    }
    $networkId = docker network ls --quiet --filter "name=^${network}$"
    if ($networkId) {
        docker network rm $networkId | Out-Null
    }
}

function Get-StatusCode {
    param([string[]]$CurlArgs)
    $result = & curl.exe --silent --show-error --insecure --output NUL --write-out "%{http_code}" @CurlArgs
    if ($LASTEXITCODE -ne 0) {
        throw "curl falhou: $($CurlArgs -join ' ')"
    }
    return [int]$result
}

function Assert-Status {
    param(
        [string]$Name,
        [int]$Expected,
        [string[]]$CurlArgs
    )
    $actual = Get-StatusCode -CurlArgs $CurlArgs
    if ($actual -ne $Expected) {
        docker logs --tail 80 $waf
        throw "$Name`: esperado HTTP $Expected, recebido $actual"
    }
    Write-Host "[OK] $Name -> HTTP $actual"
}

function Assert-JsonStatus {
    param(
        [string]$Name,
        [int]$Expected,
        [string]$Json,
        [string]$Url
    )
    $bodyFile = [System.IO.Path]::GetTempFileName()
    try {
        $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
        [System.IO.File]::WriteAllText($bodyFile, $Json, $utf8NoBom)
        Assert-Status $Name $Expected @(
            "--request", "POST",
            "--header", "Content-Type: application/json",
            "--data-binary", "@$bodyFile",
            $Url
        )
    }
    finally {
        Remove-Item -LiteralPath $bodyFile -Force -ErrorAction SilentlyContinue
    }
}

function Start-TestWaf {
    param([string]$BlocklistFile)
    docker run --detach --name $waf --network $network `
        --publish "127.0.0.1::8080" `
        --publish "127.0.0.1::8443" `
        --env SERVER_NAME=localhost `
        --env HOTEL_BACKEND_UPSTREAM="${backend}:8080" `
        --env HOTEL_FRONTEND_UPSTREAM="${backend}:8080" `
        --env MODSEC_RULE_ENGINE=On `
        --env MODSEC_AUDIT_ENGINE=RelevantOnly `
        --env MODSEC_AUDIT_LOG_PARTS=AFHZ `
        --env ACCESSLOG=/dev/null `
        --env MODSEC_REQ_BODY_LIMIT=20971520 `
        --env MODSEC_REQ_BODY_NOFILES_LIMIT=20971520 `
        --env MODSEC_RESP_BODY_ACCESS=Off `
        --env BLOCKING_PARANOIA=1 `
        --env DETECTION_PARANOIA=2 `
        --env WAF_RATE_LIMIT_DRY_RUN=off `
        --volume "${root}\waf\nginx\nginx.conf.template:/etc/nginx/templates/nginx.conf.template:ro" `
        --volume "${root}\waf\nginx\default.conf.template:/etc/nginx/templates/conf.d/default.conf.template:ro" `
        --volume "${root}\waf\nginx\proxy-backend.conf:/etc/nginx/hotel-includes/proxy-backend.conf:ro" `
        --volume "${root}\waf\nginx\proxy-frontend.conf:/etc/nginx/hotel-includes/proxy-frontend.conf:ro" `
        --volume "${root}\waf\modsecurity\modsecurity-override.conf.template:/etc/nginx/templates/modsecurity.d/modsecurity-override.conf.template:ro" `
        --volume "${root}\waf\rules:/etc/modsecurity.d/custom:ro" `
        --volume "${BlocklistFile}:/etc/nginx/waf/ip-blocklist.conf:ro" `
        $image | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Nao foi possivel iniciar o container WAF"
    }

    $httpBinding = docker port $waf 8080/tcp | Select-Object -First 1
    $httpsBinding = docker port $waf 8443/tcp | Select-Object -First 1
    if (-not $httpBinding -or -not $httpsBinding) {
        throw "Docker nao informou as portas dinamicas do WAF"
    }
    $script:httpPort = [int]($httpBinding -replace '^.*:', '')
    $script:httpsPort = [int]($httpsBinding -replace '^.*:', '')
}

function Wait-TestWaf {
    for ($attempt = 0; $attempt -lt 60; $attempt++) {
        $status = & curl.exe --silent --output NUL --write-out "%{http_code}" `
            --header "Host: localhost" "http://127.0.0.1:${httpPort}/healthz"
        if ($status -eq "200") {
            return
        }
        Start-Sleep -Seconds 1
    }
    docker logs $waf
    throw "WAF nao ficou pronto em 60 segundos"
}

Remove-TestResources

try {
    docker network create $network | Out-Null
    docker run --detach --name $backend --network $network `
        --volume "${root}\waf\tests\echo_backend.py:/app/echo_backend.py:ro" `
        python:3.12-alpine python /app/echo_backend.py | Out-Null

    Start-TestWaf "${root}\waf\ip-blocklist.conf"
    Wait-TestWaf

    $base = "https://localhost:${httpsPort}"
    $httpBase = "http://127.0.0.1:${httpPort}"
    Assert-Status "HTTP redireciona para HTTPS" 308 @(
        "--header", "Host: localhost", "${httpBase}/"
    )
    Assert-Status "scanner bloqueado tambem no HTTP" 403 @(
        "--header", "Host: localhost", "--user-agent", "sqlmap/1.9", "${httpBase}/"
    )
    Assert-Status "requisicao normal" 200 @("${base}/")
    Assert-Status "API v1 sem redirecionamento legado" 200 @("${base}/api/v1/status")
    Assert-Status "compatibilidade da API legada" 308 @("${base}/api/status")
    Assert-Status "SQL injection" 403 @("${base}/api/v1/test?id=1%20OR%201%3D1--")
    Assert-Status "XSS" 403 @("${base}/api/v1/test?q=%3Cscript%3Ealert(1)%3C%2Fscript%3E")
    Assert-Status "scanner sqlmap" 403 @("--user-agent", "sqlmap/1.9", "${base}/")
    Assert-Status "arquivo .env" 403 @("${base}/.env")
    Assert-Status "metodo TRACE" 405 @("--request", "TRACE", "${base}/")
    Assert-JsonStatus "JSON legitimo" 200 `
        '{"nome":"Maria D''Avila","observacao":"berco para bebe < 2 anos"}' `
        "${base}/api/v1/public/reservas"
    $passwordMarker = "hotelwaf-password-secret"
    Assert-JsonStatus "senha opaca com padroes de ataque" 200 `
        ('{"email":"maria@example.com","password":"' + $passwordMarker + ' OR 1=1-- <script>alert(1)</script>"}') `
        "${base}/api/v1/login"
    Assert-JsonStatus "payload TEF legitimo" 200 `
        '{"session_id":"abc","data":"{[10;16];MultiplosCupons=1;}","nfpag_raw":"NFPAG=00:3000;01:2000"}' `
        "${base}/api/v1/pagamentos/tef/continuar"

    $xffResponse = & curl.exe --silent --show-error --insecure `
        --header "X-Forwarded-For: 198.51.100.77" "${base}/xff" | ConvertFrom-Json
    if ($xffResponse.x_forwarded_for -eq "198.51.100.77") {
        throw "X-Forwarded-For enviado pelo cliente nao foi sobrescrito"
    }
    Write-Host "[OK] X-Forwarded-For forjado foi sobrescrito"

    $logMarker = "hotelwafsecret2026"
    $pathMarker = "12345678901"
    Assert-Status "access log sem path ou query sensivel" 200 @(
        "${base}/api/v1/customers/${pathMarker}?waf_log_probe=${logMarker}"
    )
    Start-Sleep -Milliseconds 200
    $previousErrorAction = $ErrorActionPreference
    try {
        $ErrorActionPreference = "Continue"
        $wafLogs = (docker logs $waf 2>&1 | Out-String)
        if ($LASTEXITCODE -ne 0) {
            throw "Nao foi possivel ler os logs do WAF"
        }
    }
    finally {
        $ErrorActionPreference = $previousErrorAction
    }
    if ($wafLogs.Contains($logMarker)) {
        throw "Access log registrou query string sensivel"
    }
    if ($wafLogs.Contains($pathMarker)) {
        throw "Access log registrou identificador sensivel do path"
    }
    if ($wafLogs.Contains($passwordMarker)) {
        throw "Audit/access log registrou conteudo de senha"
    }
    if (-not $wafLogs.Contains('"route_class":"api_v1"')) {
        throw "Access log JSON hotel_waf nao foi encontrado"
    }
    Write-Host "[OK] access log JSON omite path, query e senha"

    $rateLimited = $false
    for ($request = 0; $request -lt 20; $request++) {
        if ((Get-StatusCode @("${base}/api/v1/login")) -eq 429) {
            $rateLimited = $true
            break
        }
    }
    if (-not $rateLimited) {
        throw "Rate limit de login nao respondeu HTTP 429"
    }
    Write-Host "[OK] rate limit de login -> HTTP 429"

    docker rm --force $waf | Out-Null
    Start-TestWaf "${root}\waf\tests\ip-blocklist-all.conf"
    Wait-TestWaf
    $base = "https://localhost:${httpsPort}"
    $httpBase = "http://127.0.0.1:${httpPort}"
    Assert-Status "denylist de IP/CIDR" 403 @("${base}/")
    Assert-Status "denylist de IP/CIDR no HTTP" 403 @(
        "--header", "Host: localhost", "${httpBase}/"
    )

    Write-Host "Todos os testes WAF passaram."
}
finally {
    if (-not $KeepContainers) {
        Remove-TestResources
    }
}
