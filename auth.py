import bcrypt
import database

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def signup(username, password):
    hashed = hash_password(password)
    return database.add_user(username, hashed)

def login(username, password):
    user = database.get_user(username)
    if user and check_password(password, user[1]):
        return True
    return False
