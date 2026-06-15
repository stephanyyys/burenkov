#!/usr/bin/env python3
"""
Лабораторная работа №2: Реализация RSA
"""

import random
import math
import hashlib
from typing import Tuple

def is_prime(n: int, k: int = 5) -> bool:
    if n <= 1:
        return False
    if n <= 3:
        return True
    if n % 2 == 0:
        return False
    
    r, d = 0, n - 1
    while d % 2 == 0:
        r += 1
        d //= 2
    
    for _ in range(k):
        a = random.randint(2, n - 2)
        x = pow(a, d, n)
        if x == 1 or x == n - 1:
            continue
        for _ in range(r - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                break
        else:
            return False
    return True

def generate_prime(bits: int = 12) -> int:
    while True:
        num = random.getrandbits(bits)
        num |= (1 << bits - 1) | 1
        if is_prime(num):
            return num

def extended_gcd(a: int, b: int) -> Tuple[int, int, int]:
    if a == 0:
        return (b, 0, 1)
    else:
        g, y, x = extended_gcd(b % a, a)
        return (g, x - (b // a) * y, y)

def mod_inverse(e: int, phi: int) -> int:
    g, x, _ = extended_gcd(e, phi)
    if g != 1:
        raise ValueError("Обратный элемент не существует")
    return x % phi

def generate_rsa_keys(bits: int = 12):
    print(f"\nГенерация RSA ключей (битность: {bits})")
    print("-" * 50)
    
    p = generate_prime(bits)
    q = generate_prime(bits)
    while p == q:
        q = generate_prime(bits)
    print(f"p = {p}")
    print(f"q = {q}")
    
    n = p * q
    phi = (p - 1) * (q - 1)
    print(f"n = p * q = {n}")
    print(f"φ(n) = (p-1)*(q-1) = {phi}")
    
    e = 65537
    if e >= phi:
        e = random.randrange(2, phi)
        while math.gcd(e, phi) != 1:
            e = random.randrange(2, phi)
    print(f"e = {e}")
    
    d = mod_inverse(e, phi)
    print(f"d = {d}")
    
    print(f"\nПубличный ключ (e, n): ({e}, {n})")
    print(f"Приватный ключ (d, n): ({d}, {n})")
    
    return (e, n), (d, n)

def bytes_to_blocks(data: bytes, max_block_value: int) -> list:
    blocks = []
    current_block = 0
    bytes_in_block = 0
    
    max_bytes = (max_block_value.bit_length() - 1) // 8
    if max_bytes <= 0:
        max_bytes = 1
    
    for byte in data:
        current_block = (current_block << 8) | byte
        bytes_in_block += 1
        
        if bytes_in_block >= max_bytes:
            blocks.append(current_block)
            current_block = 0
            bytes_in_block = 0
    
    if bytes_in_block > 0:
        blocks.append(current_block)
    
    return blocks

def blocks_to_bytes(blocks: list) -> bytes:
    result = bytearray()
    for block in blocks:
        if block == 0:
            continue
        temp = block
        block_bytes = []
        while temp > 0:
            block_bytes.insert(0, temp & 0xFF)
            temp >>= 8
        result.extend(block_bytes)
    return bytes(result)

def rsa_encrypt(message: str, public_key: Tuple[int, int]) -> list:
    e, n = public_key
    message_bytes = message.encode('utf-8')
    
    print(f"\nИсходное сообщение: '{message}'")
    print(f"Длина: {len(message)} символов, {len(message_bytes)} байт")
    
    blocks = bytes_to_blocks(message_bytes, n)
    print(f"Разбито на {len(blocks)} блоков")
    print(f"Числовые блоки: {blocks}")
    
    encrypted_blocks = [pow(block, e, n) for block in blocks]
    print(f"Зашифрованные блоки: {encrypted_blocks}")
    
    return encrypted_blocks

def rsa_decrypt(encrypted_blocks: list, private_key: Tuple[int, int]) -> str:
    d, n = private_key
    decrypted_blocks = [pow(block, d, n) for block in encrypted_blocks]
    print(f"Расшифрованные блоки: {decrypted_blocks}")
    
    decrypted_bytes = blocks_to_bytes(decrypted_blocks)
    result = decrypted_bytes.decode('utf-8')
    print(f"Расшифрованное сообщение: '{result}'")
    
    return result

def rsa_sign(message: str, private_key: Tuple[int, int]) -> int:
    d, n = private_key
    hash_value = hashlib.sha256(message.encode('utf-8')).digest()
    hash_int = int.from_bytes(hash_value, 'big')
    signature = pow(hash_int, d, n)
    return signature

def rsa_verify(message: str, signature: int, public_key: Tuple[int, int]) -> bool:
    e, n = public_key
    hash_value = hashlib.sha256(message.encode('utf-8')).digest()
    hash_int = int.from_bytes(hash_value, 'big')
    decrypted_hash = pow(signature, e, n)
    hash_mod = hash_int % n
    return decrypted_hash == hash_mod

def main():
    print("=" * 60)
    print("ЛАБОРАТОРНАЯ РАБОТА №2: РЕАЛИЗАЦИЯ RSA")
    print("=" * 60)
    
    random.seed(42)
    public_key, private_key = generate_rsa_keys(bits=12)
    
    print("\n" + "=" * 50)
    print("ЧАСТЬ 1: ШИФРОВАНИЕ И ДЕШИФРОВАНИЕ")
    print("=" * 50)
    
    test_messages = [
        "Hello RSA!",
        "Mixed: English + Русский + 123",
        "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    ]
    
    success_count = 0
    for i, msg in enumerate(test_messages, 1):
        print(f"\n[{i}/{len(test_messages)}]")
        encrypted = rsa_encrypt(msg, public_key)
        decrypted = rsa_decrypt(encrypted, private_key)
        
        if msg == decrypted:
            print("Результат: УСПЕШНО")
            success_count += 1
        else:
            print(f"Результат: ОШИБКА")
    
    print(f"\nИтого: {success_count}/{len(test_messages)} успешно")
    
    print("\n" + "=" * 50)
    print("ЧАСТЬ 2: ЦИФРОВАЯ ПОДПИСЬ")
    print("=" * 50)
    
    test_docs = [
        "Важный документ",
        "Контракт №123",
        "Платёжное поручение #456"
    ]
    
    for doc in test_docs:
        print(f"\nДокумент: '{doc}'")
        signature = rsa_sign(doc, private_key)
        print(f"Подпись: {signature}")
        
        is_valid = rsa_verify(doc, signature, public_key)
        if is_valid:
            print("Проверка: ПОДЛИННЫЙ")
        else:
            print("Проверка: НЕДЕЙСТВИТЕЛЬНЫЙ")
        
        fake_doc = doc + " (изменено)"
        is_fake_valid = rsa_verify(fake_doc, signature, public_key)
        if not is_fake_valid:
            print("Атака: изменённый документ НЕ ПРОШЁЛ проверку")
    
    print("\n" + "=" * 50)
    print("ТЕХНИЧЕСКИЕ ДЕТАЛИ")
    print("=" * 50)
    e, n = public_key
    print(f"Размер ключа: {n.bit_length()} бит")
    print(f"Тест простоты: Миллера-Рабин")
    print(f"Хеш-функция: SHA-256")
    print(f"Кодировка: UTF-8")

if __name__ == "__main__":
    main()