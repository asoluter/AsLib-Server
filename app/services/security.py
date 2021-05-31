import bcrypt

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def generate_salt() -> str:
    return bcrypt.gensalt().decode()


def hash_password(password: str, salt: str) -> str:
    return pwd_context.hash(password + salt)


def verify_password(password: str, salt: str, hashed_pw: str) -> bool:
    return pwd_context.verify(password + salt, hashed_pw)
