# Salve como: criar_tabelas.py
# Execute com: python criar_tabelas.py

from app.db.base import Base, engine
from app.models import *  # Importa todos os modelos
from app.config import settings

def criar_tabelas():
    """
    Cria todas as tabelas no banco de dados
    """
    print("🔨 Criando tabelas no banco de dados...")
    print(f"📍 Conectando ao: {settings.APP_NAME}")
    print("="*60)
    
    try:
        # Criar todas as tabelas
        Base.metadata.create_all(bind=engine)
        print("✅ Tabelas criadas com sucesso!")
        
        # Listar tabelas criadas
        print("\n📋 Tabelas criadas:")
        for table in Base.metadata.tables.keys():
            print(f"   - {table}")
            
    except Exception as e:
        print(f"❌ Erro ao criar tabelas: {e}")
        print("\n💡 Dica: Verifique se o banco de dados está acessível")
    
    print("\n✨ Processo concluído!")

if __name__ == "__main__":
    criar_tabelas()