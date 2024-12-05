import bcrypt

def hash_password(password: str) -> str:
   
    salt = bcrypt.gensalt()

    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    print(hashed_password)
    return hashed_password.decode('utf-8')

hash_password("test")