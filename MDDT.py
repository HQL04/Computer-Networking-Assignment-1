# # import socket
# # import threading

# # # Giả sử có hàm download_piece(peer, piece_id) để tải một phần từ một peer cụ thể
# # def download_piece(peer, piece_id):
# #     # Kết nối tới peer để tải piece
# #     print(f"Downloading piece {piece_id} from {peer}")
# #     # Thực hiện kết nối và nhận dữ liệu...

# # # Tải xuống từ nhiều peers cùng lúc
# # def download_from_multiple_peers(piece_id, peers):
# #     threads = []
# #     for peer in peers:
# #         thread = threading.Thread(target=download_piece, args=(peer, piece_id))
# #         threads.append(thread)
# #         thread.start()
# #     for thread in threads:
# #         thread.join()

# # # Giả sử nhận được danh sách peers từ tracker
# # peers = ["peer1", "peer2", "peer3"]
# # download_from_multiple_peers("1", peers)

# import os
# import sys
# import hashlib
# CHUNK_SIZE = 512*1024
# # # Đường dẫn đến file
# # file_path = sys.argv[1]

# def read_and_hash(file_path):
#     final_path = file_path
#     hasharr =[]
#     try:
#         with open(final_path, 'rb') as f:
#             while True:
#                 chunk = f.read(CHUNK_SIZE)
#                 if not chunk: break
#                 sha1 = hashlib.sha1()
#                 sha1.update(chunk)
#                 hasharr.append(sha1.hexdigest())
#         return hasharr
#     except FileNotFoundError:
#         print("File không tồn tại")
#         return None
#     except Exception as e:
#         print(f"Lỗi khi đọc file: {e}")
#         return None

# def fileinfo(file_path):
#     if not os.path.exists(file_path): return None
#     file_size = os.path.getsize(file_path)
#     nguyen =  file_size//(CHUNK_SIZE)
#     du = file_size % CHUNK_SIZE
#     manh = 1 if du > 0 else 0
#     hash = read_and_hash(file_path)
#     if hash == None: 
#         print('Hash Error')
#         return None
#     # Đọc độ lớn của file
#     torrent = {}
#     torrent['path'] = os.path.basename(file_path)
#     torrent['size'] = file_size
#     torrent['count'] = nguyen + manh
#     torrent['lpsize'] = du
#     torrent['pieces'] = hash
#     return torrent

# peerlist = [{'id': '0', 'ip': '127.0.0.1', 'port': 10},
#             {'id': '1', 'ip': '127.0.0.1', 'port': 20},
#             {'id': '2', 'ip': '127.0.0.1', 'port': 30}
#             ]
# # threads = [] 
# for peer in peerlist: 
#     ip = peer['ip'] 
#     port = peer['port'] 
#     print(f'{ip} and {port}')
#     # arr = [0, 1, 2] # Cần thay đổi để phù hợp với các offset cần tải thực tế 
#     # t = threading.Thread(target=download, args=(ip, port, arr)) 
#     # threads.append(t) 
#     # t.start() 
# # print(fileinfo(input("nhập file_path: ")))
# # import hashlib
# # TEST = "3a586ba9732e38c5d818660866b66bde017fde9c"
# # def hash_file_sha1(filename):
# #   """Tính hash SHA-1 của một file

# #   Args:
# #     filename: Đường dẫn đến file cần tính hash

# #   Returns:
# #     Chuỗi hash SHA-1
# #   """

# #   # Mở file trong chế độ đọc nhị phân
# #   with open(filename, 'rb') as f:
# #     # Tạo một đối tượng hash SHA-1
# #     sha1 = hashlib.sha1()
# #     i = 1
# #     # Đọc từng khối dữ liệu từ file và cập nhật vào đối tượng hash
# #     while chunk := f.read(CHUNK_SIZE):
# #       print(i)
# #       sha1.update(chunk)
# #       i = i+1

# #   # Trả về chuỗi hash
# #   return sha1.hexdigest()

# # # Ví dụ sử dụng hàm
# # filename = "splitted_data/test2part_1.jpg"  # Thay thế bằng đường dẫn đến file của bạn
# # hash_value = hash_file_sha1(filename)
# # print(hash_value == TEST)
# # print("SHA-1 hash:", hash_value)

# # import numpy as np

# # arr = np.zeros(2000, dtype=str)
# # arr[1999] = "hello world"
# # print(arr[1999])

# # arr = ["" for _ in range(2000)]
# # arr[1999] = "hello world1"
# # print(arr[1999])
def extract_hash_and_offset(request_str):
    # Split the string by space
    parts = request_str.split(":")

    # Extract hash and offset based on the position in the split string
    print(parts)
    if len(parts) == 3:
        hash_value = parts[1].split(" ")[0]  # Extract the hash value after "info:"
        offset_value = int(parts[2] ) # Extract the offset after "PIECE:"
        return hash_value, offset_value
    else:
        return None, None  # Return None if the string doesn't match the expected format

# Example usage
request_str = "REQUEST info:abcdef123456 PIECE:10"
hash_value, offset_value = extract_hash_and_offset(request_str)

print("Hash:", hash_value)
print("Offset:", offset_value)
