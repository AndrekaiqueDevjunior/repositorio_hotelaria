const express = require('express');
const cors = require('cors');
const crypto = require('crypto');
const http = require('http');
const https = require('https');

const app = express();
const PORT = Number(process.env.TEF_PORT || 9999);

app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

const SERVICE_VERSION = '1.1.0-local-gateway';
const CLISITEF_VERSION = '6.2.0-sim';
const CLISITEFI_VERSION = '1.19.6-sim';

const MODE = (process.env.TEF_MODE || 'sim').toLowerCase(); // sim | real
const REAL_AGENT_URL = process.env.TEF_REAL_AGENT_URL || 'https://127.0.0.1/agente/clisitef';
const REAL_AGENT_INSECURE_TLS = String(process.env.TEF_REAL_AGENT_INSECURE_TLS || 'true').toLowerCase() === 'true';
const REAL_TIMEOUT_MS = Number(process.env.TEF_REAL_TIMEOUT_MS || 45000);

const DEFAULT_SITEF_IP = process.env.TEF_SITEF_IP || '127.0.0.1';
const DEFAULT_STORE_ID = process.env.TEF_STORE_ID || '00000000';
const DEFAULT_TERMINAL_ID = process.env.TEF_TERMINAL_ID || 'REST0001';
const DEFAULT_OPERATOR = process.env.TEF_OPERATOR || 'CAIXA';
const DEFAULT_SESSION_PARAMETERS = process.env.TEF_SESSION_PARAMETERS || '';
const DEFAULT_TRN_PARAMETERS = process.env.TEF_TRN_PARAMETERS || '';

const state = {
  serviceState: 1,
  currentSessionId: null,
  sessions: new Map(),
  transactionsBySession: new Map(),
  approvedByNsu: new Map(),
  taxInvoiceSeq: 1000,
};

function nowFiscalDate() {
  const now = new Date();
  const yyyy = String(now.getFullYear());
  const mm = String(now.getMonth() + 1).padStart(2, '0');
  const dd = String(now.getDate()).padStart(2, '0');
  return `${yyyy}${mm}${dd}`;
}

function nowFiscalTime() {
  const now = new Date();
  const hh = String(now.getHours()).padStart(2, '0');
  const mm = String(now.getMinutes()).padStart(2, '0');
  const ss = String(now.getSeconds()).padStart(2, '0');
  return `${hh}${mm}${ss}`;
}

function toReaisFromCentavos(centavos) {
  return (Number(centavos || 0) / 100).toFixed(2);
}

function generateSessionId() {
  return crypto.randomUUID();
}

function generateNsu() {
  return `NSU${Math.floor(Math.random() * 900000) + 100000}`;
}

function generateAuth() {
  return `AUT${Math.floor(Math.random() * 900000) + 100000}`;
}

function getBodyValue(req, key, fallback = undefined) {
  const value = req.body?.[key];
  if (value === undefined || value === null || value === '') return fallback;
  return value;
}

function cleanParams(data = {}, keepEmptyString = false) {
  const out = {};
  for (const [k, v] of Object.entries(data)) {
    const allow = keepEmptyString ? v !== undefined && v !== null : v !== undefined && v !== null && v !== '';
    if (allow) out[k] = v;
  }
  return out;
}

function serviceOk(extra = {}) {
  return {
    serviceStatus: 0,
    serviceMessage: 'OK',
    serviceVersion: SERVICE_VERSION,
    ...extra,
  };
}

function modeIsReal() {
  return MODE === 'real';
}

function buildAgentUrl(path, query) {
  const base = REAL_AGENT_URL.endsWith('/') ? REAL_AGENT_URL.slice(0, -1) : REAL_AGENT_URL;
  const url = new URL(`${base}${path}`);
  if (query) {
    for (const [k, v] of Object.entries(cleanParams(query))) {
      url.searchParams.set(k, String(v));
    }
  }
  return url;
}

function parseBody(text) {
  if (!text || !text.trim()) return {};
  try {
    return JSON.parse(text);
  } catch {
    return { raw: text };
  }
}

function requestAgent(method, path, data) {
  return new Promise((resolve, reject) => {
    const isGet = method.toUpperCase() === 'GET';
    const url = buildAgentUrl(path, isGet ? data : undefined);
    const payload = isGet ? '' : new URLSearchParams(cleanParams(data || {}, true)).toString();

    const options = {
      method,
      hostname: url.hostname,
      port: url.port || (url.protocol === 'https:' ? 443 : 80),
      path: `${url.pathname}${url.search}`,
      headers: {
        Accept: 'application/json, text/plain, */*',
      },
      timeout: REAL_TIMEOUT_MS,
    };

    if (!isGet) {
      options.headers['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8';
      options.headers['Content-Length'] = Buffer.byteLength(payload);
    }

    if (url.protocol === 'https:') {
      options.rejectUnauthorized = !REAL_AGENT_INSECURE_TLS;
      options.ciphers = process.env.TEF_REAL_TLS_CIPHERS || 'DEFAULT@SECLEVEL=0';
      options.minVersion = process.env.TEF_REAL_TLS_MIN_VERSION || 'TLSv1';
    }

    const lib = url.protocol === 'https:' ? https : http;
    const req = lib.request(options, (res) => {
      let raw = '';
      res.on('data', (chunk) => {
        raw += chunk;
      });
      res.on('end', () => {
        const body = parseBody(raw);
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(body);
        } else {
          reject(new Error(`HTTP ${res.statusCode}: ${raw}`));
        }
      });
    });

    req.on('timeout', () => {
      req.destroy(new Error(`Timeout ao chamar agente real (${method} ${path})`));
    });

    req.on('error', (err) => reject(err));

    if (!isGet && payload) {
      req.write(payload);
    }
    req.end();
  });
}

// ----------------------------
// SIMULADOR LOCAL (fallback)
// ----------------------------

function ensureSessionLocal({ sitefIp, storeId, terminalId, sessionParameters, existingSessionId }) {
  if (existingSessionId) {
    const existing = state.sessions.get(existingSessionId);
    if (!existing) return { error: `Sessao ${existingSessionId} nao encontrada` };
    return { session: existing, temporary: false };
  }

  const session = {
    sessionId: generateSessionId(),
    sitefIp: sitefIp || DEFAULT_SITEF_IP,
    storeId: storeId || DEFAULT_STORE_ID,
    terminalId: terminalId || DEFAULT_TERMINAL_ID,
    sessionParameters: sessionParameters || DEFAULT_SESSION_PARAMETERS,
    createdAt: new Date().toISOString(),
  };

  state.sessions.set(session.sessionId, session);
  state.currentSessionId = session.sessionId;
  return { session, temporary: true };
}

function buildCoupons({ storeId, terminalId, taxInvoiceNumber, valorCentavos, nsu, authorization }) {
  const amount = toReaisFromCentavos(valorCentavos);
  const date = nowFiscalDate();
  const time = nowFiscalTime();

  const cupomEstabelecimento = [
    'COMPROVANTE ESTABELECIMENTO',
    `LOJA: ${storeId}`,
    `TERMINAL: ${terminalId}`,
    `DOC: ${taxInvoiceNumber}`,
    `DATA: ${date} ${time}`,
    `VALOR: R$ ${amount}`,
    `NSU: ${nsu}`,
    `AUT: ${authorization}`,
    'TRANSACAO APROVADA',
  ].join('\n');

  const cupomCliente = [
    'COMPROVANTE CLIENTE',
    `LOJA: ${storeId}`,
    `DOC: ${taxInvoiceNumber}`,
    `VALOR: R$ ${amount}`,
    `NSU: ${nsu}`,
    `AUT: ${authorization}`,
    'OBRIGADO PELA PREFERENCIA',
  ].join('\n');

  return { cupomEstabelecimento, cupomCliente };
}

function createTransactionLocal({
  sessionId,
  functionId,
  trnAmount,
  taxInvoiceNumber,
  taxInvoiceDate,
  taxInvoiceTime,
  cashierOperator,
  trnAdditionalParameters,
  trnInitParameters,
  temporarySession,
}) {
  const session = state.sessions.get(sessionId);
  const valorCentavos = Number(trnAmount || 0);
  const ticket = String(taxInvoiceNumber || state.taxInvoiceSeq++);
  const date = String(taxInvoiceDate || nowFiscalDate());
  const time = String(taxInvoiceTime || nowFiscalTime());
  const operator = String(cashierOperator || DEFAULT_OPERATOR);

  const nsu = generateNsu();
  const authorization = generateAuth();
  const coupons = buildCoupons({
    storeId: session.storeId,
    terminalId: session.terminalId,
    taxInvoiceNumber: ticket,
    valorCentavos,
    nsu,
    authorization,
  });

  const menuGerencial = '1:Teste de comunicacao;2:Reimpressao de comprovante;3:Cancelamento de transacao;4:Carga de tabelas no pinpad;5:Envio de trace para o Servidor;6:Registro de Terminal';

  const steps = Number(functionId) === 110
    ? [
        {
          commandId: 21,
          data: menuGerencial,
          fieldId: 0,
          fieldMinLength: 1,
          fieldMaxLength: 1,
        },
        { commandId: 1, data: 'Menu gerencial apresentado', fieldId: 0, fieldMinLength: 0, fieldMaxLength: 0 },
        { commandId: 0, data: `FUNC=${functionId};OPERADOR=${operator}`, fieldId: 100, fieldMinLength: 0, fieldMaxLength: 1024 },
      ]
    : [
        { commandId: 30, data: 'Forneca o numero do cartao', fieldId: 0, fieldMinLength: 13, fieldMaxLength: 19 },
        { commandId: 35, data: 'Aguarde, em processamento...(35)\nForneca a data de vencimento do cartao (MMAA)', fieldId: 0, fieldMinLength: 4, fieldMaxLength: 4 },
        { commandId: 35, data: 'Aguarde, em processamento...(35)\nCodigo de Seguranca do cartao', fieldId: 0, fieldMinLength: 3, fieldMaxLength: 4 },
        {
          commandId: 30,
          data: 'Selecione a forma de pagamento\n1:A Vista\n2:Parcelado pelo Estabelecimento\n3:Parcelado pela Administradora\n4:Consulta parcelamento\n5:Consulta AVS',
          fieldId: 0,
          fieldMinLength: 1,
          fieldMaxLength: 1,
        },
        { commandId: 1, data: 'Aguarde, processando transacao...', fieldId: 0, fieldMinLength: 0, fieldMaxLength: 0 },
        { commandId: 23, data: 'Confirme no pinpad', fieldId: 0, fieldMinLength: 0, fieldMaxLength: 0 },
        { commandId: 2, data: 'Transacao em andamento', fieldId: 0, fieldMinLength: 0, fieldMaxLength: 0 },
        { commandId: 0, data: `FUNC=${functionId};VALOR=${valorCentavos};OPERADOR=${operator}`, fieldId: 100, fieldMinLength: 0, fieldMaxLength: 1024 },
        { commandId: 0, data: coupons.cupomEstabelecimento, fieldId: 121, fieldMinLength: 0, fieldMaxLength: 8000 },
        { commandId: 0, data: coupons.cupomCliente, fieldId: 122, fieldMinLength: 0, fieldMaxLength: 8000 },
      ];

  const tx = {
    sessionId,
    temporarySession,
    functionId: Number(functionId || 3),
    trnAmount: valorCentavos,
    taxInvoiceNumber: ticket,
    taxInvoiceDate: date,
    taxInvoiceTime: time,
    cashierOperator: operator,
    trnAdditionalParameters: trnAdditionalParameters || '',
    trnInitParameters: trnInitParameters || '',
    nsu,
    authorization,
    cupomEstabelecimento: coupons.cupomEstabelecimento,
    cupomCliente: coupons.cupomCliente,
    stepIndex: 0,
    steps,
    ret: [],
    finalized: false,
    approved: true,
    startedAt: new Date().toISOString(),
  };

  state.transactionsBySession.set(sessionId, tx);
  state.serviceState = 2;
  return tx;
}

function getTxLocal(sessionId) {
  return state.transactionsBySession.get(sessionId);
}

function cleanupSessionIfTemporaryLocal(tx) {
  if (!tx?.temporarySession) return;
  state.sessions.delete(tx.sessionId);
  if (state.currentSessionId === tx.sessionId) {
    state.currentSessionId = null;
  }
}

function finalizeTransactionLocal(sessionId, confirm) {
  if (!sessionId) {
    return {
      ok: false,
      payload: {
        serviceStatus: 5,
        serviceMessage: 'Nenhuma sessao disponivel para finalizar',
        serviceVersion: SERVICE_VERSION,
      },
    };
  }

  const tx = getTxLocal(sessionId);
  if (!tx) {
    return {
      ok: false,
      payload: {
        serviceStatus: 6,
        serviceMessage: 'Nenhuma transacao ativa para finalizar',
        serviceVersion: SERVICE_VERSION,
      },
    };
  }

  tx.finalized = true;
  tx.approved = Number(confirm) === 1;

  if (tx.approved) {
    state.approvedByNsu.set(tx.nsu, {
      nsu: tx.nsu,
      autorizacao: tx.authorization,
      status: 'APROVADO',
      valor: tx.trnAmount,
      cupom_estabelecimento: tx.cupomEstabelecimento,
      cupom_cliente: tx.cupomCliente,
      taxInvoiceNumber: tx.taxInvoiceNumber,
      taxInvoiceDate: tx.taxInvoiceDate,
      taxInvoiceTime: tx.taxInvoiceTime,
      finishedAt: new Date().toISOString(),
    });
  }

  state.transactionsBySession.delete(sessionId);
  cleanupSessionIfTemporaryLocal(tx);
  state.serviceState = 1;

  return {
    ok: true,
    payload: serviceOk({
      clisitefStatus: tx.approved ? 0 : -1,
      nsu: tx.nsu,
      autorizacao: tx.authorization,
      cupom_estabelecimento: tx.cupomEstabelecimento,
      cupom_cliente: tx.cupomCliente,
    }),
  };
}

async function processarPagamentoSimulado(valorCentavos) {
  const ensured = ensureSessionLocal({
    sitefIp: DEFAULT_SITEF_IP,
    storeId: DEFAULT_STORE_ID,
    terminalId: DEFAULT_TERMINAL_ID,
    sessionParameters: DEFAULT_SESSION_PARAMETERS,
    existingSessionId: null,
  });

  if (ensured.error) {
    throw new Error(ensured.error);
  }

  const tx = createTransactionLocal({
    sessionId: ensured.session.sessionId,
    functionId: 3,
    trnAmount: valorCentavos,
    taxInvoiceNumber: String(state.taxInvoiceSeq++),
    taxInvoiceDate: nowFiscalDate(),
    taxInvoiceTime: nowFiscalTime(),
    cashierOperator: DEFAULT_OPERATOR,
    trnAdditionalParameters: DEFAULT_TRN_PARAMETERS,
    trnInitParameters: DEFAULT_SESSION_PARAMETERS,
    temporarySession: true,
  });

  tx.stepIndex = tx.steps.length;

  const aprovado = Math.random() < 0.9;
  finalizeTransactionLocal(tx.sessionId, aprovado ? 1 : 0);

  if (aprovado) {
    return {
      success: true,
      aprovado: true,
      autorizacao: tx.authorization,
      nsu: tx.nsu,
      cupom_estabelecimento: tx.cupomEstabelecimento,
      cupom_cliente: tx.cupomCliente,
      mensagem: `Pagamento TEF aprovado - R$ ${toReaisFromCentavos(valorCentavos)}`,
      modo: 'sim',
    };
  }

  return {
    success: false,
    aprovado: false,
    error: 'Pagamento recusado pela maquininha',
    nsu: tx.nsu,
    mensagem: 'Transacao nao autorizada',
    modo: 'sim',
  };
}

// ----------------------------
// ORQUESTRADOR REAL
// ----------------------------

async function processarPagamentoReal(valorCentavos, reservaId) {
  const sitefIp = process.env.TEF_PAG_SITEF_IP || DEFAULT_SITEF_IP;
  const storeId = process.env.TEF_PAG_STORE_ID || DEFAULT_STORE_ID;
  const terminalId = process.env.TEF_PAG_TERMINAL_ID || DEFAULT_TERMINAL_ID;
  const cashierOperator = process.env.TEF_PAG_OPERATOR || DEFAULT_OPERATOR;
  const trnInitParameters = process.env.TEF_PAG_TRN_INIT_PARAMETERS || DEFAULT_SESSION_PARAMETERS;
  const trnAdditionalParameters = process.env.TEF_PAG_TRN_PARAMETERS || DEFAULT_TRN_PARAMETERS;

  const taxInvoiceNumber = String(state.taxInvoiceSeq++);
  const taxInvoiceDate = nowFiscalDate();
  const taxInvoiceTime = nowFiscalTime();

  const start = await requestAgent('POST', '/startTransaction', {
    sitefIp,
    storeId,
    terminalId,
    functionId: 3,
    trnAmount: valorCentavos,
    taxInvoiceNumber,
    taxInvoiceDate,
    taxInvoiceTime,
    cashierOperator,
    trnAdditionalParameters,
    trnInitParameters,
  });

  if (Number(start.serviceStatus) !== 0) {
    return {
      success: false,
      aprovado: false,
      error: `Agente retornou serviceStatus=${start.serviceStatus}`,
      detalhe: start,
      modo: 'real',
    };
  }

  if (Number(start.clisitefStatus) !== 10000) {
    return {
      success: false,
      aprovado: false,
      error: `CliSiTef nao iniciou fluxo interativo (status ${start.clisitefStatus})`,
      detalhe: start,
      modo: 'real',
    };
  }

  const sessionId = start.sessionId;
  if (!sessionId) {
    return {
      success: false,
      aprovado: false,
      error: 'Agente nao retornou sessionId no startTransaction',
      detalhe: start,
      modo: 'real',
    };
  }

  let stepCount = 0;
  let current = null;
  let nextData = '';
  let nextContinue = 0;
  let cupomEstabelecimento = '';
  let cupomCliente = '';
  let sameCommandCounter = 0;
  let lastCommandKey = '';

  while (stepCount < 120) {
    stepCount += 1;

    current = await requestAgent('POST', '/continueTransaction', {
      sessionId,
      continue: nextContinue,
      data: nextData,
    });

    nextContinue = 0;
    nextData = '';

    if (Number(current.serviceStatus) !== 0) {
      return {
        success: false,
        aprovado: false,
        error: `Erro no continueTransaction (serviceStatus=${current.serviceStatus})`,
        detalhe: current,
        modo: 'real',
      };
    }

    if (Number(current.clisitefStatus) !== 10000) {
      break;
    }

    const cmd = Number(current.commandId);
    const fieldId = Number(current.fieldId);
    const commandKey = `${cmd}:${fieldId}`;
    sameCommandCounter = commandKey === lastCommandKey ? sameCommandCounter + 1 : 0;
    lastCommandKey = commandKey;

    // Protege contra loop infinito em comando interativo sem avanço.
    if (sameCommandCounter >= 20) {
      nextContinue = -1;
      nextData = '';
      break;
    }

    if (Number(current.commandId) === 0 && Number(current.fieldId) === 121) {
      cupomEstabelecimento = String(current.data || '');
    }

    if (Number(current.commandId) === 0 && Number(current.fieldId) === 122) {
      cupomCliente = String(current.data || '');
    }

    // Respostas automáticas para o simulador/oficial em fluxo headless.
    if (cmd === 20) {
      // Comando Sim/Não: 0 = Sim
      nextData = '0';
      continue;
    }

    if ([21, 30, 31, 32, 33, 34, 35, 38].includes(cmd)) {
      const min = Math.max(0, Number(current.fieldMinLength || 0));
      const max = Math.max(min, Number(current.fieldMaxLength || min || 1));
      const len = Math.min(Math.max(min, 1), Math.max(max, 1));
      nextData = min > 0 ? '1'.repeat(Math.min(len, 12)) : '0';
      continue;
    }

    if (cmd === 23) {
      // Aguarda confirmação/cancelamento; segue fluxo normal.
      nextContinue = 0;
      nextData = '';
      continue;
    }
  }

  const clisitefFinal = Number(current?.clisitefStatus);
  const aprovado = clisitefFinal === 0 && nextContinue !== -1;

  let finish = {};
  try {
    finish = await requestAgent('POST', '/finishTransaction', {
      sessionId,
      confirm: aprovado ? 1 : 0,
      taxInvoiceNumber,
      taxInvoiceDate,
      taxInvoiceTime,
    });
  } catch (error) {
    finish = { serviceStatus: 999, serviceMessage: error.message };
  }

  const nsu = finish.nsu || current?.nsu || `NSU-SEM-${reservaId}`;
  const autorizacao = finish.autorizacao || current?.autorizacao || null;

  if (aprovado) {
    const cupomEstabFinal = finish.cupom_estabelecimento || cupomEstabelecimento;
    const cupomCliFinal = finish.cupom_cliente || cupomCliente;

    state.approvedByNsu.set(nsu, {
      nsu,
      autorizacao,
      status: 'APROVADO',
      valor: valorCentavos,
      cupom_estabelecimento: cupomEstabFinal,
      cupom_cliente: cupomCliFinal,
      taxInvoiceNumber,
      taxInvoiceDate,
      taxInvoiceTime,
      finishedAt: new Date().toISOString(),
      modo: 'real',
    });

    return {
      success: true,
      aprovado: true,
      autorizacao,
      nsu,
      cupom_estabelecimento: cupomEstabFinal,
      cupom_cliente: cupomCliFinal,
      mensagem: `Pagamento TEF aprovado - R$ ${toReaisFromCentavos(valorCentavos)}`,
      modo: 'real',
    };
  }

  return {
    success: false,
    aprovado: false,
    nsu,
    error: `Transacao nao autorizada (clisitefStatus=${clisitefFinal})`,
    mensagem: 'Transacao nao autorizada',
    detalhe_continue: current,
    detalhe_finish: finish,
    modo: 'real',
  };
}

async function proxyOrFallback(req, res, method, path) {
  if (modeIsReal()) {
    try {
      const payload = method === 'GET' ? req.query : req.body;
      const data = await requestAgent(method, path, payload);
      return res.json(data);
    } catch (error) {
      return res.status(502).json({
        serviceStatus: 900,
        serviceMessage: `Falha no agente real: ${error.message}`,
        serviceVersion: SERVICE_VERSION,
      });
    }
  }
  return null;
}

// ----------------------------
// Endpoints
// ----------------------------

app.get('/health', async (req, res) => {
  if (!modeIsReal()) {
    return res.json({ status: 'OK', mode: 'sim', service: 'TEF Agente CliSiTef (local)' });
  }

  try {
    const data = await requestAgent('GET', '/state', {});
    res.json({
      status: 'OK',
      mode: 'real',
      service: 'TEF Agente CliSiTef (proxy)',
      agente: {
        serviceStatus: data.serviceStatus,
        serviceState: data.serviceState,
        serviceVersion: data.serviceVersion,
      },
    });
  } catch (error) {
    res.status(502).json({
      status: 'ERROR',
      mode: 'real',
      service: 'TEF Agente CliSiTef (proxy)',
      error: error.message,
    });
  }
});

app.get('/state', async (req, res) => {
  const proxied = await proxyOrFallback(req, res, 'GET', '/state');
  if (proxied !== null) return;

  res.json(serviceOk({
    serviceState: state.serviceState,
    sessionId: state.currentSessionId,
  }));
});

app.post('/session', async (req, res) => {
  const proxied = await proxyOrFallback(req, res, 'POST', '/session');
  if (proxied !== null) return;

  const sessionId = generateSessionId();
  const session = {
    sessionId,
    sitefIp: getBodyValue(req, 'sitefIp', DEFAULT_SITEF_IP),
    storeId: getBodyValue(req, 'storeId', DEFAULT_STORE_ID),
    terminalId: getBodyValue(req, 'terminalId', DEFAULT_TERMINAL_ID),
    sessionParameters: getBodyValue(req, 'sessionParameters', DEFAULT_SESSION_PARAMETERS),
    createdAt: new Date().toISOString(),
  };

  state.sessions.set(sessionId, session);
  state.currentSessionId = sessionId;
  state.serviceState = 1;

  res.json(serviceOk({ sessionId }));
});

app.get('/session', async (req, res) => {
  const proxied = await proxyOrFallback(req, res, 'GET', '/session');
  if (proxied !== null) return;

  if (!state.currentSessionId || !state.sessions.has(state.currentSessionId)) {
    return res.json({
      serviceStatus: 1,
      serviceMessage: 'Nenhuma sessao ativa',
      serviceVersion: SERVICE_VERSION,
    });
  }

  const session = state.sessions.get(state.currentSessionId);
  res.json(serviceOk({
    sessionId: session.sessionId,
    sitefIp: session.sitefIp,
    storeId: session.storeId,
    terminalId: session.terminalId,
  }));
});

app.delete('/session', async (req, res) => {
  const proxied = await proxyOrFallback(req, res, 'DELETE', '/session');
  if (proxied !== null) return;

  if (state.currentSessionId) {
    state.sessions.delete(state.currentSessionId);
    state.transactionsBySession.delete(state.currentSessionId);
    state.currentSessionId = null;
  }
  state.serviceState = 1;
  res.json(serviceOk({ message: 'Sessao finalizada' }));
});

app.post('/getVersion', async (req, res) => {
  const proxied = await proxyOrFallback(req, res, 'POST', '/getVersion');
  if (proxied !== null) return;

  res.json(serviceOk({
    clisitefVersion: CLISITEF_VERSION,
    clisitefiVersion: CLISITEFI_VERSION,
  }));
});

app.post('/startTransaction', async (req, res) => {
  const proxied = await proxyOrFallback(req, res, 'POST', '/startTransaction');
  if (proxied !== null) return;

  if (Array.from(state.transactionsBySession.values()).some((tx) => !tx.finalized)) {
    return res.json({
      serviceStatus: 98,
      serviceMessage: 'Agente ocupado com outra transacao',
      serviceVersion: SERVICE_VERSION,
    });
  }

  const sessionIdFromBody = getBodyValue(req, 'sessionId');
  const ensured = ensureSessionLocal({
    sitefIp: getBodyValue(req, 'sitefIp'),
    storeId: getBodyValue(req, 'storeId'),
    terminalId: getBodyValue(req, 'terminalId'),
    sessionParameters: getBodyValue(req, 'sessionParameters') || getBodyValue(req, 'trnInitParameters'),
    existingSessionId: sessionIdFromBody,
  });

  if (ensured.error) {
    return res.json({
      serviceStatus: 2,
      serviceMessage: ensured.error,
      serviceVersion: SERVICE_VERSION,
    });
  }

  const tx = createTransactionLocal({
    sessionId: ensured.session.sessionId,
    functionId: getBodyValue(req, 'functionId', 3),
    trnAmount: getBodyValue(req, 'trnAmount', 0),
    taxInvoiceNumber: getBodyValue(req, 'taxInvoiceNumber'),
    taxInvoiceDate: getBodyValue(req, 'taxInvoiceDate'),
    taxInvoiceTime: getBodyValue(req, 'taxInvoiceTime'),
    cashierOperator: getBodyValue(req, 'cashierOperator', DEFAULT_OPERATOR),
    trnAdditionalParameters: getBodyValue(req, 'trnAdditionalParameters', DEFAULT_TRN_PARAMETERS),
    trnInitParameters: getBodyValue(req, 'trnInitParameters', DEFAULT_SESSION_PARAMETERS),
    temporarySession: ensured.temporary,
  });

  state.currentSessionId = tx.sessionId;

  res.json(serviceOk({
    sessionId: tx.sessionId,
    clisitefStatus: 10000,
  }));
});

app.post('/continueTransaction', async (req, res) => {
  const proxied = await proxyOrFallback(req, res, 'POST', '/continueTransaction');
  if (proxied !== null) return;

  const sessionId = getBodyValue(req, 'sessionId');
  const cont = Number(getBodyValue(req, 'continue', 0));
  const data = String(getBodyValue(req, 'data', ''));

  if (!sessionId) {
    return res.json({
      serviceStatus: 3,
      serviceMessage: 'sessionId obrigatorio',
      serviceVersion: SERVICE_VERSION,
    });
  }

  const tx = getTxLocal(sessionId);
  if (!tx) {
    return res.json({
      serviceStatus: 4,
      serviceMessage: 'Transacao nao encontrada para a sessao',
      serviceVersion: SERVICE_VERSION,
    });
  }

  if (cont === -1) {
    tx.approved = false;
    tx.finalized = true;
    cleanupSessionIfTemporaryLocal(tx);
    state.transactionsBySession.delete(sessionId);
    state.serviceState = 1;

    return res.json(serviceOk({
      clisitefStatus: -2,
      commandId: 0,
      fieldId: 0,
      fieldMinLength: 0,
      fieldMaxLength: 0,
      data: 'Operacao cancelada pelo operador',
    }));
  }

  if (tx.stepIndex < tx.steps.length) {
    const step = tx.steps[tx.stepIndex++];
    if (step.commandId === 0) {
      tx.ret.push({ fieldId: step.fieldId, data: step.data });
    }

    state.serviceState = tx.stepIndex >= tx.steps.length ? 4 : 3;

    return res.json(serviceOk({
      clisitefStatus: 10000,
      commandId: step.commandId,
      fieldId: step.fieldId,
      fieldMinLength: step.fieldMinLength,
      fieldMaxLength: step.fieldMaxLength,
      data: step.data,
      inputData: data,
    }));
  }

  state.serviceState = 4;
  return res.json(serviceOk({
    clisitefStatus: 0,
    commandId: 0,
    fieldId: 0,
    fieldMinLength: 0,
    fieldMaxLength: 0,
    data: '',
  }));
});

app.post('/finishTransaction', async (req, res) => {
  const proxied = await proxyOrFallback(req, res, 'POST', '/finishTransaction');
  if (proxied !== null) return;

  const sessionId = getBodyValue(req, 'sessionId') || state.currentSessionId;
  const confirm = Number(getBodyValue(req, 'confirm', 1));

  const result = finalizeTransactionLocal(sessionId, confirm);
  res.json(result.payload);
});

app.post('/pinpad/open', async (req, res) => {
  const proxied = await proxyOrFallback(req, res, 'POST', '/pinpad/open');
  if (proxied !== null) return;
  res.json(serviceOk({ clisitefStatus: 0 }));
});

app.post('/pinpad/close', async (req, res) => {
  const proxied = await proxyOrFallback(req, res, 'POST', '/pinpad/close');
  if (proxied !== null) return;
  res.json(serviceOk({ clisitefStatus: 0 }));
});

app.post('/pinpad/isPresent', async (req, res) => {
  const proxied = await proxyOrFallback(req, res, 'POST', '/pinpad/isPresent');
  if (proxied !== null) return;
  res.json(serviceOk({ clisitefStatus: 1 }));
});

app.post('/pinpad/setDisplayMessage', async (req, res) => {
  const proxied = await proxyOrFallback(req, res, 'POST', '/pinpad/setDisplayMessage');
  if (proxied !== null) return;
  res.json(serviceOk({ clisitefStatus: 0 }));
});

app.post('/pinpad/readYesNo', async (req, res) => {
  const proxied = await proxyOrFallback(req, res, 'POST', '/pinpad/readYesNo');
  if (proxied !== null) return;
  res.json(serviceOk({ clisitefStatus: 1 }));
});

app.post('/pagamento', async (req, res) => {
  try {
    const valor = Number(getBodyValue(req, 'valor'));
    const reservaId = getBodyValue(req, 'reserva_id');

    if (!valor || !reservaId) {
      return res.status(400).json({
        success: false,
        error: 'Valor e reserva_id sao obrigatorios',
      });
    }

    if (modeIsReal()) {
      const resultadoReal = await processarPagamentoReal(valor, reservaId);
      return res.json(resultadoReal);
    }

    const resultadoSim = await processarPagamentoSimulado(valor);
    return res.json(resultadoSim);
  } catch (error) {
    console.error('Erro no pagamento TEF:', error);
    res.status(500).json({
      success: false,
      error: error.message || 'Erro interno no pagamento TEF',
    });
  }
});

app.get('/consulta/:nsu', (req, res) => {
  const { nsu } = req.params;
  const found = state.approvedByNsu.get(nsu);

  if (!found) {
    return res.status(404).json({
      success: false,
      status: 'NAO_ENCONTRADO',
      mensagem: 'NSU nao localizado',
    });
  }

  res.json({
    success: true,
    status: found.status,
    autorizacao: found.autorizacao,
    mensagem: found.status === 'CANCELADO' ? 'Pagamento cancelado' : 'Pagamento aprovado',
  });
});

app.post('/cancelamento/:nsu', (req, res) => {
  const { nsu } = req.params;
  const found = state.approvedByNsu.get(nsu);

  if (!found) {
    return res.status(404).json({
      success: false,
      mensagem: 'NSU nao localizado para cancelamento',
    });
  }

  found.status = 'CANCELADO';
  found.canceledAt = new Date().toISOString();

  res.json({
    success: true,
    mensagem: 'Cancelamento realizado com sucesso',
  });
});

app.listen(PORT, () => {
  console.log(`TEF Agente Service rodando na porta ${PORT}`);
  console.log(`Modo: ${MODE}`);
  console.log(`Agente real: ${REAL_AGENT_URL}`);
});

process.on('SIGINT', () => {
  console.log('Encerrando TEF Agente Service...');
  process.exit(0);
});
