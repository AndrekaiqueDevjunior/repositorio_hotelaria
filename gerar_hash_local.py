import bcrypt

# Gerar hash para senha local
password_local = 'rKKv0FibuygVioryw0GJD87C2n'
new_hash_local = bcrypt.hashpw(password_local.encode('utf-8'), bcrypt.gensalt(rounds=12))

print("=== HASH PARA BANCO LOCAL ===")
print(f"Senha: {password_local}")
print(f"Hash: {new_hash_local.decode('utf-8')}")
print(f"\nSQL para atualizar:")
print(f"UPDATE funcionarios SET senha = '{new_hash_local.decode('utf-8')}' WHERE email = 'admin@hotelreal.com.br';")

# Verificar
test = bcrypt.checkpw(password_local.encode('utf-8'), new_hash_local)
print(f"\nVerificação: {test}")
