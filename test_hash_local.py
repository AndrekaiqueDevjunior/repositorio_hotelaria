import bcrypt

# Senha do .env local
password_local = 'rKKv0FibuygVioryw0GJD87C2n'
hash_local = '$2b$12$ghKr6/82nEo/G08puTuhJesZex9vQD9/cKpzj.MiGbqfXRpzq0qY6'

# Senha do .env.production
password_prod = 'nlSbJlfMjZ9OGZa1zwCED7bLaZ8Hg3zT'
hash_prod = '$2b$12$LDlZS2ehalnaUSDgMV/Vne2Gak.Mw/OHCMZs/fFIx5nKy6dsLAhMq'

print("=== TESTE LOCAL ===")
try:
    result_local = bcrypt.checkpw(password_local.encode('utf-8'), hash_local.encode('utf-8'))
    print(f"Senha local '{password_local}' com hash local: {result_local}")
except Exception as e:
    print(f"ERRO local: {e}")

print("\n=== TESTE PRODUÇÃO ===")
try:
    result_prod = bcrypt.checkpw(password_prod.encode('utf-8'), hash_prod.encode('utf-8'))
    print(f"Senha prod '{password_prod}' com hash prod: {result_prod}")
except Exception as e:
    print(f"ERRO prod: {e}")

print("\n=== GERAR NOVO HASH PARA PRODUÇÃO ===")
try:
    new_hash = bcrypt.hashpw(password_prod.encode('utf-8'), bcrypt.gensalt(rounds=12))
    print(f"Novo hash para '{password_prod}':")
    print(new_hash.decode('utf-8'))
    
    # Testar o novo hash
    test = bcrypt.checkpw(password_prod.encode('utf-8'), new_hash)
    print(f"Verificação do novo hash: {test}")
except Exception as e:
    print(f"ERRO ao gerar: {e}")
