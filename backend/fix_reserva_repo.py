"""
Script para corrigir o arquivo reserva_repo.py
"""

# Ler o arquivo atual
with open('app/repositories/reserva_repo.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Encontrar e corrigir a seção problemática
# A linha 282-291 está corrompida

# Texto corrompido a ser substituído
old_text = '''                raise ValueError(
                    f"⏳ CONFIRMAÇÃO EM ANÁLISE! Esta reserva possui risco {analise.get('risco')} "
        
    # Atualizar status da reserva (ambos os campos)
    await self.db.reserva.update(
        where={"id": reserva_id},
        data={
            "status": "CONFIRMADA",
            "status_reserva": "CONFIRMADA"
            raise ValueError("Reserva não encontrada")
        
        # Não permite editar reservas já finalizadas
        if reserva.status in ("CHECKED_OUT", "CANCELADO"):
            raise ValueError("Não é possível editar reservas finalizadas ou canceladas")'''

# Texto correto
new_text = '''                raise ValueError(
                    f"⏳ CONFIRMAÇÃO EM ANÁLISE! Esta reserva possui risco {analise.get('risco')} "
                    f"e está em período de análise anti-fraude. "
                    f"Aguarde {horas_restantes:.1f} horas ou aprove manualmente. "
                    f"Score de risco: {analise.get('score')}"
                )
        
        # Atualizar status da reserva (ambos os campos)
        await self.db.reserva.update(
            where={"id": reserva_id},
            data={
                "status": "CONFIRMADA",
                "status_reserva": "CONFIRMADA"
            }
        )
        
        updated_reserva = await self.db.reserva.find_unique(where={"id": reserva_id})
        
        # Criar hospedagem se não existir
        hospedagem_existente = await self.db.hospedagem.find_unique(
            where={"reservaId": reserva_id}
        )
        
        if not hospedagem_existente:
            await self.db.hospedagem.create(
                data={
                    "reservaId": reserva_id,
                    "statusHospedagem": "NAO_INICIADA"
                }
            )
            print(f"✅ Hospedagem criada para reserva {reserva_id}")
        
        # Gerar voucher automaticamente após confirmação
        try:
            from app.services.voucher_service import VoucherService
            voucher_service = VoucherService(self.db)
            voucher = await voucher_service.gerar_voucher(reserva_id)
            print(f"✅ Voucher gerado: {voucher.get('codigo')}")
        except Exception as e:
            print(f"⚠️ Erro ao gerar voucher: {e}")
        
        # Criar notificação de confirmação
        await NotificationService.notificar_reserva_confirmada(updated_reserva)
        
        return self._serialize_reserva(updated_reserva)
    
    async def update(self, reserva_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Atualizar dados gerais da reserva"""
        reserva = await self.db.reserva.find_unique(where={"id": reserva_id})
        if not reserva:
            raise ValueError("Reserva não encontrada")
        
        # Não permite editar reservas já finalizadas
        if reserva.status in ("CHECKED_OUT", "CANCELADO"):
            raise ValueError("Não é possível editar reservas finalizadas ou canceladas")'''

# Substituir
if old_text in content:
    content = content.replace(old_text, new_text)
    print("✅ Correção aplicada com sucesso!")
else:
    print("⚠️ Texto não encontrado, tentando correção alternativa...")
    # Tentar encontrar apenas a parte crítica
    if "raise ValueError(\"Reserva não encontrada\")" in content and "status_reserva" in content:
        # Fazer correção manual linha por linha
        lines = content.split('\n')
        corrected_lines = []
        skip_until = -1
        
        for i, line in enumerate(lines):
            if skip_until > i:
                continue
                
            if 'raise ValueError("Reserva não encontrada")' in line and i > 280 and i < 295:
                # Encontrou a linha problemática, substituir toda a seção
                corrected_lines.append('            }')
                corrected_lines.append('        )')
                corrected_lines.append('        ')
                corrected_lines.append('        updated_reserva = await self.db.reserva.find_unique(where={"id": reserva_id})')
                corrected_lines.append('        ')
                corrected_lines.append('        # Criar hospedagem se não existir')
                corrected_lines.append('        hospedagem_existente = await self.db.hospedagem.find_unique(')
                corrected_lines.append('            where={"reservaId": reserva_id}')
                corrected_lines.append('        )')
                corrected_lines.append('        ')
                corrected_lines.append('        if not hospedagem_existente:')
                corrected_lines.append('            await self.db.hospedagem.create(')
                corrected_lines.append('                data={')
                corrected_lines.append('                    "reservaId": reserva_id,')
                corrected_lines.append('                    "statusHospedagem": "NAO_INICIADA"')
                corrected_lines.append('                }')
                corrected_lines.append('            )')
                corrected_lines.append('            print(f"✅ Hospedagem criada para reserva {reserva_id}")')
                corrected_lines.append('        ')
                corrected_lines.append('        # Gerar voucher automaticamente após confirmação')
                corrected_lines.append('        try:')
                corrected_lines.append('            from app.services.voucher_service import VoucherService')
                corrected_lines.append('            voucher_service = VoucherService(self.db)')
                corrected_lines.append('            voucher = await voucher_service.gerar_voucher(reserva_id)')
                corrected_lines.append('            print(f"✅ Voucher gerado: {voucher.get(\'codigo\')}")')
                corrected_lines.append('        except Exception as e:')
                corrected_lines.append('            print(f"⚠️ Erro ao gerar voucher: {e}")')
                corrected_lines.append('        ')
                corrected_lines.append('        # Criar notificação de confirmação')
                corrected_lines.append('        await NotificationService.notificar_reserva_confirmada(updated_reserva)')
                corrected_lines.append('        ')
                corrected_lines.append('        return self._serialize_reserva(updated_reserva)')
                corrected_lines.append('    ')
                corrected_lines.append('    async def update(self, reserva_id: int, data: Dict[str, Any]) -> Dict[str, Any]:')
                corrected_lines.append('        """Atualizar dados gerais da reserva"""')
                corrected_lines.append('        reserva = await self.db.reserva.find_unique(where={"id": reserva_id})')
                corrected_lines.append('        if not reserva:')
                corrected_lines.append('            raise ValueError("Reserva não encontrada")')
                skip_until = i + 10  # Pular as próximas linhas corrompidas
            elif skip_until <= i:
                corrected_lines.append(line)
        
        content = '\n'.join(corrected_lines)
        print("✅ Correção alternativa aplicada!")

# Salvar arquivo corrigido
with open('app/repositories/reserva_repo.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Arquivo salvo com sucesso!")
