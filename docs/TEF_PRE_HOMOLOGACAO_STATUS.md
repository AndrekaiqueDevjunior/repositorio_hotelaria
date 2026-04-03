# Status de Pre-Homologacao TEF

Data de consolidacao: 30/03/2026

## Ambiente validado

- Agente ativo: `AgenteCliSiTef 1.0.0.16 r1 Simulado Win64`
- Backend em modo real apontando para `https://host.docker.internal/agente/clisitef`
- SiTef local: `127.0.0.1`
- Empresa valida: `00000000`
- Terminal valido: `REST0001`

## Fechado para adiantar a pre-homologacao

### Seq. 1 - Menu 110 completo

Status: `ADIANTADA`

Evidencias:
- menu `110` abriu corretamente;
- opcao `Registro de Terminal` ficou visivel apos habilitacao de `4178` no `CliSiTef.ini`;
- `110 -> 14` chegou ao prompt `Token registro de terminal`.

### Seq. 3 - Falha de configuracao / Nao Existe Conf

Status: `ADIANTADA`

Evidencias:
- com `storeId=1111AAAA`, o fluxo atingiu `Nao existe conf.`;
- nao houve autorizacao nem cupom.

### Seq. 21 - TLS Fiserv

Status: `ADIANTADA`

Evidencias:
- a funcao `699` foi exercitada no agente;
- o fluxo chegou ao pedido de token de registro;
- o envio de parametros TLS ficou demonstrado na integracao.

Limite atual:
- ainda sem `TokenRegistro` real de Fiserv, entao o registro real do terminal segue dependente do provedor.

## Executadas hoje e resultado real

### Seq. 2 - Timeout com SitDemo fechado

Status: `NAO FECHADA`

Resultado real:
- o `SitDemo.exe` foi encerrado;
- a funcao `3` abriu normalmente;
- o fluxo caiu em `31 - Erro Pinpad` antes de atingir o timeout esperado do roteiro.

Conclusao:
- no ambiente atual, a Seq. 2 esta contaminada pelo problema de pinpad e nao pode ser dada como fechada.

### Seq. 17 - Venda QR Code

Status: `BLOQUEADA POR HABILITACAO DE AMBIENTE`

Resultado real:
- a funcao `122` respondeu imediatamente com `Carteira Digital - Trn. nao habilitada`.

Conclusao:
- a transacao QR Code nao esta habilitada neste ambiente.
- nao depende do pinpad, mas depende de habilitacao do provedor/ambiente.

### Seq. 18 - Cancelamento QR Code

Status: `BLOQUEADA POR HABILITACAO DE AMBIENTE`

Resultado real:
- a funcao `123` abriu e pediu supervisor;
- com a senha correta do ambiente, o fluxo prosseguiu;
- logo em seguida retornou `Carteira Digital - Trn. nao habilitada`.

Conclusao:
- o cancelamento QR tambem esta bloqueado pela falta de habilitacao da carteira digital no ambiente.

### Seq. 19 - Tratamento de pendencias

Status: `EXECUTADA PARCIALMENTE`

Resultado real:
- a rotina `resolver_pendencias(confirmar=True)` executou com sucesso;
- retorno obtido: `success=true`, `clisitef_status=0`, `serviceStatus=0`.

Conclusao:
- a trilha tecnica de tratamento de pendencias esta operacional;
- ainda falta simular uma pendencia real para fechar o item do roteiro com evidencia completa de confirmacao/desfazimento.

## Aguardando chaves PIN PAD para testar

Estas sequencias dependem de interacao real com a maquininha e devem permanecer com o status:

`Aguardando chaves PIN PAD para testar`

### Evidencia tecnica do bloqueio atual

- o Windows reconhece `Gertec PIN Pad PPC (COM3)`;
- o `CliSiTef.ini` ativo foi ajustado para `Porta=03`;
- mesmo assim, o agente continua retornando:
  - `pinpad/isPresent -> clisitefStatus=0`
  - `pinpad/open -> clisitefStatus=30`

Interpretacao:
- o hardware existe no Windows;
- a CliSiTef nao reconhece/abre o equipamento como pinpad TEF utilizavel.

### Sequencias afetadas por pinpad

- Seq. 4 - Credito negado acima de R$ 25.000,00
- Seq. 5 - Debito com chip a partir de R$ 10,00
- Seq. 6 - Credito a vista com chip a partir de R$ 15,00
- Seq. 7 - Credito parcelado pelo estabelecimento
- Seq. 8 - Credito parcelado pela administradora
- Seq. 9 - Cancelamento durante a venda
- Seq. 10 - Voltar ao menu anterior
- Seq. 11 - Timeout de 60 segundos por tela
- Seq. 14 - Cancelamento da transacao de debito
- Seq. 15 - Cancelamento da transacao de credito
- Seq. 22 - Multiplos pagamentos com troco em dinheiro
- Seq. 23 - Multiplos pagamentos com dois cartoes
- Seq. 24 - Multiplos pagamentos com carteira digital

## Resumo honesto do que pode seguir agora

### Pode ser usado para adiantar a pre-homologacao

- Seq. 1
- Seq. 3
- Seq. 21

### Foi executado, mas ainda nao pode ser dado como fechado

- Seq. 2
- Seq. 19

### Bloqueado por habilitacao de ambiente

- Seq. 17
- Seq. 18

### Bloqueado por pinpad

- Seq. 4 a 11
- Seq. 14
- Seq. 15
- Seq. 22 a 24

## Proxima ordem recomendada

1. Usar `Seq. 1`, `Seq. 3` e `Seq. 21` como evidencias atuais de pre-homologacao.
2. Registrar `Seq. 2` como nao fechada no ambiente atual porque o pinpad interfere antes do timeout esperado.
3. Registrar `Seq. 17` e `Seq. 18` como bloqueadas por `Carteira Digital - Trn. nao habilitada`.
4. Manter `Seq. 19` como executada parcialmente ate simular uma pendencia real.
5. Manter `Seq. 4 a 11`, `14`, `15`, `22`, `23` e `24` como `Aguardando chaves PIN PAD para testar`.
