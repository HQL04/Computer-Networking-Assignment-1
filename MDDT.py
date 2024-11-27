import socket
import threading
import os
import sys
import hashlib
CHUNK_SIZE = 512*1024
CLIENT = sys.argv[1]

def correct_path(file_path):
    current_file_path = os.path.dirname(os.path.abspath(__file__)) #lấy thư mục cha của thư mục chạy file code
    finalpath = f"{current_file_path}/{CLIENT}/{file_path}" #lấy path theo client
    return finalpath

def splitfile(source, target):
    target = correct_path(target)[:-1]
    print(target)
    global arrname
    with open(source, 'rb') as f_in:
        part = 0
        while True:
            data = f_in.read(CHUNK_SIZE)
            if not data: break
            newfile = f"{target}/{arrname[part]}"  # Add the file extension
            with open(newfile, 'wb') as f_out: f_out.write(data)
            part += 1

def mergefile( arr_name, resultfile):
    path = correct_path('')
    try:
        resultfile = path + resultfile
        with open(resultfile, 'wb') as fout:
            for name in arr_name:
                try:
                    name = path + name
                    print(name)
                    with open(name, 'rb') as f:
                        fout.write(f.read())
                except FileNotFoundError: print('file not found')
    except Exception as e: print(e)
        
# test = 'test2.jpg'
# folder = ''
# arrname = ['abc','xyz']
# # splitfile( test, folder)
# target = 'abcxyz.jpg'
# mergefile(arrname, target)
def generate_bitfield(num_pieces, downloaded_pieces):
    """
    Tạo bitfield cho peer, với số lượng pieces tổng cộng và danh sách các pieces đã tải.
    
    :param num_pieces: Tổng số lượng pieces của tệp.
    :param downloaded_pieces: Danh sách các chỉ số của các pieces đã tải (ví dụ [0, 2, 5] có nghĩa là peer đã tải pieces 0, 2, 5).
    :return: Bitfield dưới dạng một chuỗi nhị phân.
    """
    # Khởi tạo bitfield với tất cả các bit là 0
    bitfield = ['0'] * num_pieces
    
    # Đặt bit tương ứng với các pieces đã tải thành 1
    for piece in downloaded_pieces:
        if 0 <= piece < num_pieces:
            bitfield[piece] = '1'
    
    # Chuyển đổi list bitfield thành một chuỗi nhị phân
    return ''.join(bitfield)

def save_bitfield_to_file(bitfield, filename):
    """
    Lưu bitfield vào một tệp.
    
    :param bitfield: Chuỗi nhị phân đại diện cho bitfield.
    :param filename: Tên tệp để lưu bitfield.
    """
    with open(filename, 'wb') as f:
        # Convert bitfield string to bytes
        byte_array = int(bitfield, 2).to_bytes((len(bitfield) + 7) // 8, byteorder='big')
        f.write(byte_array)

# Ví dụ sử dụng
# num_pieces = 10  # Ví dụ tệp có 10 pieces
# downloaded_pieces = [0, 2, 5]  # Peer đã tải các pieces 0, 2, 5
# bitfield = generate_bitfield(num_pieces, downloaded_pieces)
# print("Bitfield:", bitfield)

# Lưu bitfield vào file
# save_bitfield_to_file(bitfield, "peer_bitfield.dat")

def create_empty_file(filename, n):
    """
    Tạo một tệp tin rỗng với kích thước n byte.
    
    :param filename: Tên tệp tin cần tạo.
    :param n: Kích thước của tệp tin (tính bằng byte).
    """
    with open(filename, 'wb') as f:
        f.write(b'\x00' * n)  # Ghi n byte có giá trị 0 vào tệp tin

# Ví dụ sử dụng
create_empty_file('empty_file.txt', 1024)  # Tạo tệp tin rỗng có kích thước 1024 byte
def write_at_offset(filename, offset, data):
    with open(filename, 'r+b') as file:
        file.seek(offset)
        file.write(data)
        
write_at_offset('empty_file.txt', 5, b'\x01') 