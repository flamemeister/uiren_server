import random
import string

def generate_random_password(length=8):
    return ''.join(random.choices(string.digits, k=length))
