import random
import string

def generate_random_password(length=8):
    # Генерация случайного пароля из цифр
    return ''.join(random.choices(string.digits, k=length))
