# Checklist TEF - Pre-homologacao (Hotel Real)

Data base: 2026-04-14

## 1) Preparacao do ambiente
- Confirmar backend no ar: `http://localhost:18000/health` deve retornar `status=healthy`.
- Confirmar agente CliSiTef acessivel em `https://127.0.0.1/agente/clisitef`.
- Confirmar timezone fiscal:
  - `TEF_TIMEZONE=America/Sao_Paulo` no backend.
  - Hora enviada em `taxInvoiceTime` deve bater com horario local do PDV.

## 2) Configuracao TLS (quando solicitado no roteiro)
No `CliSiTef.ini`:
- `TipoComunicacaoExterna=TLSGWP`
- `ConfiguraEnderecoIP=tls-prod.fiservapp.com`
- Proxy (se houver): `GwpTipoProxy` e `GwpEnderecoProxy`
- Registro de terminal: `TokenRegistro` (somente quando aplicavel)

Observacoes do documento TLS 1.06:
- URL nova: `tls-prod.fiservapp.com`
- Porta nova: `443`
- Se legado estiver em `postls-prod.fiservapp.com:4096`, a CliSiTef pode atualizar automaticamente.

## 3) Sequencia obrigatoria de testes
1. Venda credito (modalidade 3 ou 0, conforme roteiro)
2. Venda debito (modalidade 2)
3. Cancelamento
4. Cancelamento carteira digital / Pix
5. Tratamento de pendencias (funcao 130)
6. Multiplos pagamentos
7. Teste TLS Fiserv

## 4) Regras de validacao por teste
- Sempre enviar `Finaliza` apos `Retorno = 0`.
- `cupomFiscal` deve ser unico por transacao (nao reutilizar em erro/cancelamento seguinte).
- `Horario` deve estar no fuso local correto (sem diferenca de 3h).
- Cancelamento de carteira digital/Pix:
  - usar o valor retornado no `TipoCampo 4077` (NSU Host).
- Multiplos pagamentos:
  - enviar `Finaliza` apenas na ultima transacao do lote.

## 5) Teste de pendencias (queda de energia)
1. Iniciar venda (credito ou debito).
2. No momento em que aparecer "transacao aprovada", encerrar a automacao rapidamente (simulando falha).
3. Reiniciar automacao.
4. Executar consulta/tratamento de pendencias (funcao 130).
5. Finalizar pendencia com `confirm=1` (ou `0` para desfazer, quando o roteiro pedir).
6. Na `Finaliza` da funcao 130, usar os campos retornados pela propria pendencia: `160` como CupomFiscal, `163` como DataFiscal e `164` como Horario.
7. Guardar logs mostrando:
   - campos 210/160/161/163/164/211/1319 no fluxo 130
   - chamada de `FinalizaFuncaoSiTefInterativo` apos o tratamento.

## 6) Evidencias para reenviar
- Logs em `.txt` de cada sequencia (credito, debito, cancelamento, pix, pendencia, multiplos, tls).
- Print/trecho mostrando `TipoCampo=4077` no cancelamento Pix.
- Print/trecho mostrando `Finaliza` apos `Retorno=0`.
- Print/trecho mostrando cupom fiscal unico por transacao.
- Print/trecho mostrando horario fiscal correto.

## 7) Conversao de trace (.dmp -> .txt)
- Descompactar `_01AbreTraceCliente.zip`.
- Arrastar o arquivo `.dmp` do dia para um dos executaveis do pacote.
- Usar o `.txt` gerado para validacao final e envio.
