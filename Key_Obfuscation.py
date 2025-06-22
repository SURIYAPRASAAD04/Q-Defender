import random
from typing import Dict, Tuple
from qiskit import QuantumCircuit, transpile
from qiskit_aer import Aer
import math
import secrets

min_range, max_range = 1, 26 

def generate_random_bits(n):
    qc = QuantumCircuit(1, 1)
    qc.h(0)
    qc.measure(0, 0)
    simulator = Aer.get_backend('qasm_simulator')
    return [list(simulator.run(qc, shots=1).result().get_counts().keys())[0] for _ in range(n)]

def random_number(bits):
    return int(''.join(bits), 2)

def number_of_bits_required():
    return math.ceil(math.log(max_range - min_range + 1, 2))

def random_number_between(min_val, max_val):
    random_num = max_val + 1
    while random_num > max_val:
        random_bits = generate_random_bits(number_of_bits_required())
        random_num = random_number(random_bits) + min_val
    return random_num

def QRNG():
    return random_number_between(min_range, max_range)


def generate_clock_tables() -> Dict[int, Dict[bytes, bytes]]:
    
    clock_tables = {}
    all_bytes = bytes(range(256))  
    
    for table_num in range(1, 27):
        shuffled = list(all_bytes)
        
        random.seed(secrets.randbits(42) + table_num)
        random.shuffle(shuffled)
        
       
        table = {
            original.to_bytes(1, 'big'): new.to_bytes(1, 'big')
            for original, new in zip(all_bytes, shuffled)
            if original != new
        }
        clock_tables[table_num] = table
    
    return clock_tables

CLOCK_TABLES = generate_clock_tables()


def transform_bytes(input_bytes: bytes, table_num1: int, table_num2: int) -> Tuple[bytes, dict]:
    if not input_bytes:
        return b'', {'original_length': 0}

    half = len(input_bytes) // 2
    first_half = input_bytes[:half]
    second_half = input_bytes[half:]

    table1 = CLOCK_TABLES[table_num1]
    table2 = CLOCK_TABLES[table_num2]

    transformed_first = b''.join([table1.get(bytes([b]), bytes([b])) for b in first_half])
    transformed_second = b''.join([table2.get(bytes([b]), bytes([b])) for b in second_half])

    metadata = {
        'original_length': len(input_bytes),
        'half_point': half
    }

    full_transformed = bytes([table_num1]) + bytes([table_num2]) + transformed_first + transformed_second

    return full_transformed, metadata


def reconstruct_bytes(transformed_bytes: bytes, metadata: dict) -> bytes:
    if metadata['original_length'] == 0:
        return b''

    table_num1 = transformed_bytes[0]
    table_num2 = transformed_bytes[1]

    table1 = {v: k for k, v in CLOCK_TABLES[table_num1].items()}
    table2 = {v: k for k, v in CLOCK_TABLES[table_num2].items()}

    half = metadata['half_point']
    first_half = transformed_bytes[2:2+half]
    second_half = transformed_bytes[2+half:]

    original_first = b''.join([table1.get(bytes([b]), bytes([b])) for b in first_half])
    original_second = b''.join([table2.get(bytes([b]), bytes([b])) for b in second_half])

    return original_first + original_second


def jumble_bytes(data: bytes, levels: list) -> Tuple[bytes, dict]:
    padding_info = {}
    for level in levels:
        
        pad_len = (level - len(data) % level) % level
        if pad_len:
            data += b'\xFF' * pad_len
            padding_info[level] = pad_len
        
        chunks = [data[i:i+level] for i in range(0, len(data), level)]
        data = b''.join(chunks[::-1])
    
    return data, padding_info

def reconstruct_jumbled(jumbled_data: bytes, levels: list, padding_info: dict) -> bytes:
    for level in reversed(levels):
       
        chunks = [jumbled_data[i:i+level] for i in range(0, len(jumbled_data), level)]
        jumbled_data = b''.join(chunks[::-1])
        
       
        if level in padding_info:
            jumbled_data = jumbled_data[:-padding_info[level]]
    
    return jumbled_data



transformed,metadata = b'',{}
levels = [7, 11, 23]  
jumbled_data,padding_info =  b'',{}
final_data = 0

def Obfuscate(original_data):
    global transformed, metadata, jumbled_data, padding_info



    jumbled_data, padding_info = jumble_bytes(original_data, levels)
 
    table_num1, table_num2 = QRNG(), QRNG()
    print(f"\nUsing Clock Tables: {table_num1} and {table_num2}")

    transformed, metadata = transform_bytes(jumbled_data, table_num1, table_num2)
    print("\n=== After Transformation ===")
    return transformed


def Clarify(transformed):
    half = (len(transformed) - 2) // 2 
    metadata2 = {
        'original_length': len(transformed) - 2,
        'half_point': half
    }
    reconstructed = reconstruct_bytes(transformed, metadata2)

    global final_data
    final_data = reconstruct_jumbled(reconstructed, levels, padding_info)
    return final_data

