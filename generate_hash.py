import bcrypt
password = 'JSNIKDHJUOPLjnsodpsaud09p32hj20921hdy80@##*HfjçNHHçjsh'
salt = bcrypt.gensalt(rounds=12)
hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
print(hashed.decode('utf-8'))
