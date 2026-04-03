# TEF - Erro 70 (Modo Invalido)

Data: 03/04/2026

## Sintoma

No PIN PAD aparece:

`70 - Modo Invalido. Retire e Passe o Cartao`

E, na pratica, nenhum cartao e aprovado.

## Leitura tecnica (com base na documentacao do projeto)

Quando esse comportamento acontece para todos os cartoes, a causa mais provavel nao e "cartao ruim", e sim bloqueio de ambiente TEF/PIN PAD:

1. Pinpad nao aberto corretamente pela CliSiTef (ou sem chave de operacao).
2. Equipamento/ambiente forcando modo diferente do esperado para a transacao.
3. Parametros de loja/terminal/registro incompletos.

No projeto, ja existe evidencia de bloqueio de PIN PAD em pre-homologacao:

- `pinpad/isPresent -> clisitefStatus=0`
- `pinpad/open -> clisitefStatus=30`

Quando isso ocorre, o ambiente pode reconhecer o hardware no Windows, mas ainda nao operar o fluxo de cartao com chip.

## Checklist objetivo de correcao

1. Confirmar comunicacao basica do TEF:
   - `SiTef`, `storeId`, `terminalId` e operador preenchidos com os dados validos do provedor.
2. Validar status do PIN PAD no agente:
   - `isPresent` deve responder equipamento presente.
   - `open` deve abrir sem erro.
3. Revisar configuracao ativa do `CliSiTef.ini`:
   - porta correta do equipamento (evitar divergencia entre `AUTO_USB` e `COMxx` real em uso).
4. Executar carga/atualizacao de tabelas no PIN PAD (menu gerencial TEF).
5. Garantir registro do terminal/token TLS concluido no ambiente correto.
6. Repetir teste com transacao de chip simples (debito ou credito a vista).

## Quando escalar para o provedor TEF

Escalar imediatamente para habilitacao de ambiente/chaves quando:

- todos os cartoes falham com a mesma mensagem de modo invalido;
- PIN PAD aparece no Windows, mas nao completa fluxo TEF com chip;
- apos carga de tabelas e validacao de porta, o erro persiste.

## Referencias internas usadas nesta revisao

- `docs/TEF_PRE_HOMOLOGACAO_STATUS.md`
- `_tmp_docx_roteiro/_all_text.txt`
- `SDK - Agente CliSiTef Windows/CliSiTef.ini`
