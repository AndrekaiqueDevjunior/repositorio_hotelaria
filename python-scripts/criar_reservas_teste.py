import asyncio
import requests
from datetime import datetime, timedelta

async def criar_reservas_via_api():
    try:
        # Login para obter token
        login_data = {
            'email': 'admin@hotelreal.com.br',
            'password': 'admin123'
        }
        
        session = requests.Session()
        login_response = session.post('http://localhost:8000/api/v1/login', json=login_data)
        
        if login_response.status_code != 200:
            print('❌ Erro no login:', login_response.text)
            return
        
        login_result = login_response.json()
        user_name = login_result.get("user", {}).get("nome", "N/A")
        print('🔐 Login realizado com sucesso!')
        print(f'   User: {user_name}')
        print()
        
        # O sistema usa cookies, o session já deve manter os cookies automaticamente
        
        # Dados das 5 reservas com diferentes cenários
        reservas_data = [
            {
                'cliente_id': 2,
                'quarto_numero': '102',
                'tipo_suite': 'STANDARD',
                'checkin_previsto': (datetime.now() - timedelta(days=2)).isoformat(),
                'checkout_previsto': (datetime.now() - timedelta(days=1)).isoformat(),
                'valor_diaria': 200.0,
                'num_diarias': 1
            },
            {
                'cliente_id': 3,
                'quarto_numero': '103',
                'tipo_suite': 'LUXO',
                'checkin_previsto': (datetime.now() - timedelta(days=1)).isoformat(),
                'checkout_previsto': datetime.now().isoformat(),
                'valor_diaria': 300.0,
                'num_diarias': 1
            },
            {
                'cliente_id': 4,
                'quarto_numero': '104',
                'tipo_suite': 'SUITE',
                'checkin_previsto': datetime.now().isoformat(),
                'checkout_previsto': (datetime.now() + timedelta(days=1)).isoformat(),
                'valor_diaria': 400.0,
                'num_diarias': 1
            },
            {
                'cliente_id': 5,
                'quarto_numero': '105',
                'tipo_suite': 'STANDARD',
                'checkin_previsto': (datetime.now() + timedelta(days=1)).isoformat(),
                'checkout_previsto': (datetime.now() + timedelta(days=2)).isoformat(),
                'valor_diaria': 200.0,
                'num_diarias': 1
            },
            {
                'cliente_id': 6,
                'quarto_numero': '201',
                'tipo_suite': 'LUXO',
                'checkin_previsto': (datetime.now() + timedelta(days=2)).isoformat(),
                'checkout_previsto': (datetime.now() + timedelta(days=3)).isoformat(),
                'valor_diaria': 300.0,
                'num_diarias': 2
            }
        ]
        
        print('🏨 CRIANDO 5 RESERVAS VIA API...')
        print()
        
        reservas_criadas = []
        
        for i, reserva_data in enumerate(reservas_data, 1):
            try:
                cliente_id = reserva_data['cliente_id']
                print(f'{i}. Criando reserva para cliente {cliente_id}...')
                
                response = session.post('http://localhost:8000/api/v1/reservas', json=reserva_data)
                
                if response.status_code == 201:
                    reserva = response.json()
                    codigo = reserva.get('codigo_reserva')
                    reserva_id = reserva.get('id')
                    print(f'   ✅ Reserva criada: {codigo} (ID: {reserva_id})')
                    reservas_criadas.append(reserva)
                else:
                    print(f'   ❌ Erro ao criar reserva: {response.text}')
                    
            except Exception as e:
                print(f'   ❌ Erro na requisição: {e}')
        
        print()
        print(f'Total de reservas criadas: {len(reservas_criadas)}')
        print()
        
        # Listar todas as reservas
        response = session.get('http://localhost:8000/api/v1/reservas')
        if response.status_code == 200:
            data = response.json()
            print('📋 TODAS AS RESERVAS NO BANCO:')
            for reserva in data.get('reservas', []):
                codigo = reserva.get('codigo_reserva')
                status = reserva.get('status')
                cliente = reserva.get('cliente_nome')
                print(f'  {codigo} - Status: {status} - Cliente: {cliente}')
        
    except Exception as e:
        print('ERRO GERAL:', e)
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(criar_reservas_via_api())
