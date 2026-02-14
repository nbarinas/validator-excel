from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

try:
    password = "admin"
    hashed = get_password_hash(password)
    print(f"Hashed password: {hashed}")
    is_valid = verify_password(password, hashed)
    print(f"Password valid: {is_valid}")
    print("SUCCESS: bcrypt is working correctly with passlib.")
except Exception as e:
    print(f"FAILURE: {e}")
