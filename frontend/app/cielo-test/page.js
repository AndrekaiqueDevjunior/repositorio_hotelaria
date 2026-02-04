"use client";

import { useState, useEffect } from "react";
import { useToast } from "../../contexts/ToastContext";

export default function CieloTestPage() {
  const { addToast } = useToast();
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState(null);
  const [resultado, setResultado] = useState(null);
  const [paymentId, setPaymentId] = useState("");

  const [formData, setFormData] = useState({
    // Dados do Cliente
    nome_completo: "CLIENTE TESTE PRODUCAO",
    email: "teste@hotelreal.com.br",
    cpf: "12345678901",
    telefone: "11999999999",
    
    // Dados do Cartão
    cartao_numero: "4242424242424242",
    cartao_nome: "CLIENTE TESTE PRODUCAO",
    cartao_validade: "12/2025",
    cartao_cvv: "123"
  });

  // Verificar status Cielo ao carregar
  useEffect(() => {
    checkStatus();
  }, []);

  const checkStatus = async () => {
    try {
      const response = await fetch("/api/v1/cielo-test/status");
      const data = await response.json();
      setStatus(data);
    } catch (error) {
      addToast({
        titulo: "Erro",
        mensagem: "Erro ao verificar status Cielo",
        tipo: "error"
      });
      console.error(error);
    }
  };

  const handleInputChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const testarPagamento = async () => {
    setLoading(true);
    setResultado(null);

    try {
      addToast({
        titulo: "Processando",
        mensagem: "Processando pagamento de R$ 1,00...",
        tipo: "info"
      });

      const response = await fetch("/api/v1/cielo-test/pagamento-1-real", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(formData)
      });

      const data = await response.json();

      if (data.success) {
        addToast({
          titulo: "Sucesso",
          mensagem: "✅ Pagamento aprovado!",
          tipo: "success"
        });
        setResultado(data);
        setPaymentId(data.cielo_response?.payment_id || "");
      } else {
        addToast({
          titulo: "Erro",
          mensagem: `❌ Pagamento falhou: ${data.error}`,
          tipo: "error"
        });
        setResultado(data);
      }
    } catch (error) {
      addToast({
        titulo: "Erro",
        mensagem: "Erro de conexão",
        tipo: "error"
      });
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const testarEstorno = async () => {
    if (!paymentId) {
      addToast({
        titulo: "Erro",
        mensagem: "Nenhum payment ID disponível para estorno",
        tipo: "error"
      });
      return;
    }

    setLoading(true);
    try {
      addToast({
        titulo: "Processando",
        mensagem: "Processando estorno...",
        tipo: "info"
      });

      const response = await fetch(`/api/v1/cielo-test/estorno-teste?payment_id=${paymentId}`, {
        method: "POST"
      });

      const data = await response.json();

      if (data.success) {
        addToast({
          titulo: "Sucesso",
          mensagem: "✅ Estorno processado!",
          tipo: "success"
        });
        setResultado(data);
      } else {
        addToast({
          titulo: "Erro",
          mensagem: `❌ Estorno falhou: ${data.error}`,
          tipo: "error"
        });
        setResultado(data);
      }
    } catch (error) {
      addToast({
        titulo: "Erro",
        mensagem: "Erro no estorno",
        tipo: "error"
      });
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const limparTestes = async () => {
    setLoading(true);
    try {
      addToast({
        titulo: "Processando",
        mensagem: "Limpando dados de teste...",
        tipo: "info"
      });

      const response = await fetch("/api/v1/cielo-test/limpar-testes");
      const data = await response.json();

      if (data.success) {
        addToast({
          titulo: "Sucesso",
          mensagem: "✅ Dados limpos!",
          tipo: "success"
        });
        setResultado(data);
        setPaymentId("");
      } else {
        addToast({
          titulo: "Erro",
          mensagem: `❌ Erro: ${data.error}`,
          tipo: "error"
        });
      }
    } catch (error) {
      addToast({
        titulo: "Erro",
        mensagem: "Erro ao limpar",
        tipo: "error"
      });
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            🧪 Testes Cielo Produção
          </h1>
          <p className="text-gray-600">
            Teste integração real com Cielo usando pagamento de R$ 1,00
          </p>
        </div>

        {/* Status Cielo */}
        {status && (
          <div className={`rounded-lg p-4 mb-6 ${
            status.success ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'
          }`}>
            <h3 className="font-semibold mb-2">Status Cielo</h3>
            <div className="text-sm space-y-1">
              <p><strong>Ambiente:</strong> {status.mode}</p>
              <p><strong>Merchant ID:</strong> {status.merchant_id}</p>
              <p><strong>API URL:</strong> {status.api_url}</p>
              <p><strong>Credenciais OK:</strong> {status.credentials_ok ? '✅' : '❌'}</p>
            </div>
          </div>
        )}

        {/* Formulário de Teste */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">📝 Dados do Pagamento Teste</h2>
          
          {/* Dados do Cliente */}
          <div className="mb-6">
            <h3 className="text-lg font-medium mb-3 text-gray-800">👤 Dados do Cliente</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Nome Completo *
                </label>
                <input
                  type="text"
                  name="nome_completo"
                  value={formData.nome_completo}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Seu nome completo"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Email
                </label>
                <input
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="seu@email.com"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  CPF *
                </label>
                <input
                  type="text"
                  name="cpf"
                  value={formData.cpf}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="000.000.000-00"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Telefone *
                </label>
                <input
                  type="text"
                  name="telefone"
                  value={formData.telefone}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="(11) 99999-9999"
                />
              </div>
            </div>
          </div>
          
          {/* Dados do Cartão */}
          <div className="mb-6">
            <h3 className="text-lg font-medium mb-3 text-gray-800">💳 Dados do Cartão</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Número do Cartão
                </label>
                <input
                  type="text"
                  name="cartao_numero"
                  value={formData.cartao_numero}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="4242424242424242"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Validade
                </label>
                <input
                  type="text"
                  name="cartao_validade"
                  value={formData.cartao_validade}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="12/2025"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  CVV
                </label>
                <input
                  type="text"
                  name="cartao_cvv"
                  value={formData.cartao_cvv}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="123"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Nome no Cartão
                </label>
                <input
                  type="text"
                  name="cartao_nome"
                  value={formData.cartao_nome}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="NOME COMPLETO"
                />
              </div>
            </div>
          </div>

          <div className="mt-6">
            <button
              onClick={testarPagamento}
              disabled={loading}
              className="bg-blue-600 text-white px-6 py-3 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
            >
              {loading ? "Processando..." : "🚀 Testar Pagamento R$ 1,00"}
            </button>
          </div>
        </div>

        {/* Ações Adicionais */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">⚡ Ações Rápidas</h2>
          
          <div className="flex flex-wrap gap-3">
            <button
              onClick={testarEstorno}
              disabled={loading || !paymentId}
              className="bg-orange-600 text-white px-4 py-2 rounded-md hover:bg-orange-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              💸 Estornar R$ 1,00
            </button>
            
            <button
              onClick={limparTestes}
              disabled={loading}
              className="bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              🗑️ Limpar Testes
            </button>
            
            <button
              onClick={checkStatus}
              disabled={loading}
              className="bg-gray-600 text-white px-4 py-2 rounded-md hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              🔄 Verificar Status
            </button>
          </div>
        </div>

        {/* Resultados */}
        {resultado && (
          <div className={`rounded-lg p-6 ${
            resultado.success ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'
          }`}>
            <h3 className="text-lg font-semibold mb-3">
              {resultado.success ? '✅ Sucesso' : '❌ Erro'}
            </h3>
            <div className="space-y-2">
              <pre className="text-sm bg-white p-3 rounded border overflow-auto">
                {JSON.stringify(resultado, null, 2)}
              </pre>
            </div>
          </div>
        )}

        {/* Instruções */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold mb-3">📋 Como Usar</h3>
          <ol className="list-decimal list-inside space-y-2 text-sm">
            <li>Faça login no sistema</li>
            <li>Preencha os dados do cliente (campos obrigatórios marcados com *)</li>
            <li>Preencha os dados do cartão de teste</li>
            <li>Clique em "Testar Pagamento R$ 1,00"</li>
            <li>Verifique se R$ 1,00 foi debitado do seu cartão</li>
            <li>Teste o estorno para validar processo completo</li>
            <li>Use "Limpar Testes" para remover dados criados</li>
          </ol>
          
          <div className="mt-4 p-3 bg-yellow-100 rounded">
            <p className="text-sm">
              <strong>⚠️ Atenção:</strong> Este é um ambiente de PRODUÇÃO real. 
              O pagamento de R$ 1,00 será processado e debitado.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
