import socket
import threading
import os
import sys
import shutil
import re
import subprocess
import json
from urllib.parse import urlparse
import random
import hashlib
import requests

CHUNK_SIZE = 512*1024  # size of each piece 512 KB
CLIENT = sys.argv[1]
SOCKET = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # socket để kết nối tracker
LISOCK = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # socket để lắng nghe yêu cầu các peer
FLAG_LISTEN = True
TRACKER_URL = 'http://localhost:5000'
PEER_ID = None

def readatline(ten_file, n):
    if n <= 0: return ""

    if not os.path.isfile(ten_file):
        print(f"File '{ten_file}' not found.")
        return ""

    i = 1 
    res = ""
    with open(ten_file, 'r') as file:
        for line in file:
            if i == n:
                res = line
                break
            i += 1
    return res

def bind_port(host, port):
  try:
    LISOCK.bind((host, port))
    print(f"Port {port} on {host} is open")
    return True
  except OSError as e:
    print(f"Error binding port {port}: {e}")
    return False

def natural_sort(file_list):
    convert = lambda text: int(text) if text.isdigit() else text
    alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)]
    return sorted(file_list, key=alphanum_key)

# Split file and keep the extension
def splitfile(source, target):
    file_name, file_extension = os.path.splitext(source)  # Get file name and extension
    fname = os.path.basename(file_name)
    with open(source, 'rb') as f_in:
        part = 1
        while True:
            data = f_in.read(CHUNK_SIZE)
            if not data:
                break
            newfile = f"{target}/{fname}part_{part}{file_extension}"  # Add the file extension
            with open(newfile, 'wb') as f_out:
                f_out.write(data)
            part += 1

# Link the parts of the file
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
                
def create_folder(folder_name):
  # Lấy đường dẫn đến thư mục hiện tại
  current_dir = os.getcwd()
  # Tạo đường dẫn đầy đủ đến thư mục mới
  new_folder_path = os.path.join(current_dir, folder_name)
  # Tạo thư mục
  try:
    os.makedirs(new_folder_path)
    print(f"Thư mục '{folder_name}' đã được tạo thành công tại: {new_folder_path}")
  except FileExistsError:
    print(f"Thư mục '{folder_name}' đã tồn tại.")

def read_metadata(file_path):
    """Đọc metadata từ file JSON"""
    with open(file_path, 'r') as f:
        metadata = json.load(f)
    return metadata

def parse_announce_url(announce_url):
    """Phân tích URL để lấy host và port"""
    parsed_url = urlparse(announce_url)
    host = parsed_url.hostname  # Lấy host (localhost)
    port = parsed_url.port  # Lấy port (5000)
    return host, port

def send(type, msg):
    try:
        if type.lower() == "json":
            encoded_msg = json.dumps(msg).encode()
        else:
            encoded_msg = msg.encode()
        SOCKET.sendall(encoded_msg)
    except Exception as e:
        print(f"Error occurred: {e}")

def receive():
    data = b''
    while True:
        part = SOCKET.recv(CHUNK_SIZE)
        if not part: break
        data += part
        if b'\n' or b'}' in part: break
    data = data.decode() 
    # data = SOCKET.recv(1024).decode()
    return data

def correct_path(file_path):
    current_file_path = os.path.dirname(os.path.abspath(__file__)) #lấy thư mục cha của thư mục chạy file code
    finalpath = f"{current_file_path}/{CLIENT}/{file_path}" #lấy path theo client
    return finalpath

def read_and_hash(file_path):
    final_path = correct_path(file_path)
    hash_str = ""
    try:
        with open(final_path, 'rb') as f:
            while chunk := f.read(CHUNK_SIZE):  # Đọc từng piece
                sha1 = hashlib.sha1()
                sha1.update(chunk)  # Tính SHA-1 của piece
                hash_str += sha1.hexdigest()  # Thêm hash của piece vào chuỗi
        return hash_str  # Trả về chuỗi hash của toàn bộ file (piece-wise)
    except FileNotFoundError:
        print("File không tồn tại")
        return ""
    except Exception as e:
        print(f"Lỗi khi đọc file: {e}")
        return ""

def fileinfo(file_path):
    final_path = correct_path(file_path)
    if not os.path.exists(final_path): return None

    file_size = os.path.getsize(final_path)    
    nguyen =  file_size//(CHUNK_SIZE)
    du = file_size % CHUNK_SIZE
    manh = 1 if du > 0 else 0
    hash = read_and_hash(file_path)
    if hash == "": 
        print('Hash Error')
        return None
    # Đọc độ lớn của file
    torrent = {}
    torrent['path']     = os.path.basename(final_path)
    torrent['size']     = file_size
    torrent['count']    = nguyen + manh
    torrent['pieces']   = hash
    return torrent

def upload(url,file_path): # transmission-create
    # upload gồm path, size, count, lpsize, pieces 
    torrent = fileinfo(file_path)
    # SOCKET.listen()
    if torrent == None: return False
    print(torrent)
    url = url + '/upload'
    # send("json",torrent)
    hashdata = hashlib.sha1(json.dumps(torrent).encode()).hexdigest()
    torrent['info'] = hashdata
    torrent['id'] = PEER_ID
    # print(type(torrent))
    res = requests.post(url, json = torrent).json()
    print(res)
    if res['message'] == "Need to login": return False
    
    # print(data)
    data = res['data']
    path = correct_path("table.json") 
    table = {}
    if os.path.exists(path): 
        with open(f'{path}', 'r') as file:
            table = json.load(file)
    print(table)
    table[f'{data['info']}'] = file_path # Ghi lại nội dung vào tệp JSON 
    with open(f'{path}', 'w') as file: json.dump(table, file, indent=4)
    return True

def register(url):
    path = correct_path("peer_id.txt")
    ip, port = LISOCK.getsockname()
    try:
        if os.path.exists(path): # nếu file có tồn tại thì lấy thông tin từ file mà login vào hệ thống p2p
            with open(path, 'r') as file: 
                id = file.readline()[:-1]
                ip = file.readline()[:-1]
                port = file.readline()
            url = url +'/login'
            msg = {
                "id": id,
                "ip": ip,
                "port": port
            }
            res = requests.post(url,json= msg).json()
            # print(res['i)
            global PEER_ID
            PEER_ID = id
        else: # nếu không tồn tại thì gửi thông điệp và nhận lại peer_id sau đó ghi vào file peer_id.txt
            url = url +'/register'
            msg = {
                "ip": ip,
                "port": port
            }
            res = requests.post(url,json= msg).json()
            id = res['id']
            PEER_ID = id
            with open(path, 'w') as file:
                file.write(f"{id}\n")
                file.write(f"{ip}\n")
                file.write(f"{port}\n")
        print(res)
    except Exception as e:
        print(f"Đã xảy ra lỗi tại register: {e}")

def stop():
    SOCKET.sendall("STOP".encode())
    global FLAG_LISTEN
    FLAG_LISTEN = False 

def extract_request(request_str):
    # Split the string by space
    parts = request_str.split(":")

    # Extract hash and offset based on the position in the split string
    # print(parts)
    if len(parts) == 3:
        hash_value = parts[1].split(" ")[0]  # Extract the hash value after "info:"
        offset_value = int(parts[2] ) # Extract the offset after "PIECE:"
        return hash_value, offset_value
    else:
        return None, None  # Return None if the string doesn't match the expected format

def read_piece(file_path, piece_index):
    try:
        with open(file_path, 'rb') as file:
            file.seek(piece_index * CHUNK_SIZE)  # Assuming CHUNK_SIZE is defined globally
            return file.read(CHUNK_SIZE)  # Read the chunk of the file
    except Exception as e:
        print(f'lỗi tại read piece:{e}')
        
def handle_peer_request(conn, addr):
    handshake = False
    while True:
        data = conn.recv(1024).decode()  # Receive request data from peer
        # request = json.loads(data)  # Decode the JSON request
        print(f'data: {data}')
        if data.startswith("HANDSHAKE") : # HANDSHAKE:abcxyz -> info
            print("handshake")
            info = data.split(":")[1]
            if info.endswith("\n"): info = info.strip("\n")
            
            path = correct_path("table.json")
            with open(path,'r') as f: table = json.load(f)
            
            if info in table: # ACCEPTED:1111111111111111111111111111111111
                bitfield = table[info]['bitfield']
                if bitfield.endswith("\n"): bitfield = bitfield.strip("\n")
                conn.send((f"ACCEPTED:{bitfield}").encode()) # trả về trường bitfield giúp xác định piece nào mà peer được yêu cầu đang có
                handshake  = True          
            else:
                conn.send("REJECTED".encode())           
        elif handshake and data.startswith("REQUEST") :  # Check if the request type is "REQUEST"
            hash, offset = extract_request(data)
            # print (f'hash:{type(hash)} và offset:{type(offset)}')
            path = correct_path("table.json")
            # print(f'path:{path}')
            with open(path,'r') as f: table = json.load(f)
            # print(table)
            file_name = correct_path(table[hash]['path'])
            # print(file_name)
            piece = offset
            piece_data = read_piece(file_name, piece)
            conn.send(piece_data)
        elif (not handshake) and data.startswith("REQUEST") :
            conn.send("NEED TO HANDSHAKE".encode())
        else: 
            # conn.send("ERROR".encode())
            handshake = False
            print("STOP")
            break
    
    # conn.close()

def listen_for_peers():
    LISOCK.listen()
    print(f"Listening on port {PORT}")
    global FLAG_LISTEN
    while FLAG_LISTEN:
        conn, addr = LISOCK.accept()
        threading.Thread(target=handle_peer_request, args=(conn, addr)).start()

def write_at_offset(filename, offset, data):
    with open(filename, 'r+b') as file:
        file.seek(offset*CHUNK_SIZE)
        file.write(data)

def download(ip, port, hash, arr, path): # arr chứa offset của các piece mà thread sẽ tải
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((ip,port))
    request = f"HANDSHAKE:{hash}" 
    s.sendall(request.encode()) 
    res = s.recv(CHUNK_SIZE).decode()
    if res.startswith("REJECTED"): return # bỏ qua peer này
    elif res.startswith("ACCEPTED"): #ACCEPTED:1111111111111111111111111111111111
        bitfield = res.split(':')[1]
        print(f"port:{port} & bitfield:{bitfield}")
        for offset in arr:
            request = f"REQUEST info:{hash} PIECE:{offset}" 
            s.sendall(request.encode()) 
            response = s.recv(CHUNK_SIZE) 
            print(f"Received piece {offset} of {hash}")
            # print(response)
            write_at_offset(path, offset, response)
        # with lock:  # Ensure that updates to downarr are thread-safe
        #     downarr[offset*CHUNK_SIZE:offset*CHUNK_SIZE + len(response)] = response  # Save the response at the correct offset
    s.sendall("END".encode())
    s.close()

def request(hash, metadata):
    # nhớ gửi peer_id
    msg = {
        "info": hash,
        "id": PEER_ID
    }
    url = TRACKER_URL + '/request'
    res = requests.get(url, json= msg).json()
    print(res['data'])
    peerlist = res['data']
    if(len(peerlist) == 0): return
    downloadfile(hash, metadata, peerlist)

def downloadfile(hash, metadata, peerlist):
    numpiece = metadata['count'] # 34
    numthread = min( numpiece , len(peerlist) ) # 34 vs 20 => 20
    if numthread > 20: numthread = 20 # giới hạn số thread
    quo, rem = divmod( numpiece, numthread) # quo >= 1
    
    with open(correct_path(metadata['path']), 'wb') as f:
        f.write(b'\x00' * metadata['size'])  # Ghi n byte có giá trị 0 vào tệp tin
    
    offset = list(range(numpiece))  # toạ mảng từ 0 đến n-1 => có n mảnh
    random.shuffle(offset)          # random chọn offset cho các peer
    random.shuffle(peerlist)        # random chọn peer để tải
    threads = [] 
    arrindex = 0
    # downarr = bytearray(metadata['size'])
    # lock = threading.Lock()
    for i in range (numthread):
        peer = peerlist[i] 
        ip = peer['ip'] 
        port = peer['port'] 
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((ip,port))
        request = f"HANDSHAKE:{hash}" 
        s.sendall(request.encode()) 
        res = s.recv(CHUNK_SIZE).decode()
        if res.startswith("REJECTED"): continue # bỏ qua peer này
        elif res.startswith("ACCEPTED"): #ACCEPTED:1111111111111111111111111111111111
            bitfield = res.split(':')[1]
            print(f"port:{port} & bitfield:{bitfield}")
        else: continue
        s.close()
        
        if rem > 0 :  
            rem -= 1
            asize = quo + 1
        else : asize = quo
        arr = offset[arrindex : arrindex + asize]
        arrindex += asize
        t = threading.Thread(target=download, args=( ip, port, hash, arr, correct_path(metadata['path']) )) 
        threads.append(t) 
        t.start() 
        
    for t in threads: 
        t.join()


    # with open(correct_path(metadata['path']), 'wb') as file:
    #     file.write(downarr)
    # Tạo thư mục chứa file nếu chưa tồn tại
    table_path = correct_path("table.json")
    os.makedirs(os.path.dirname(table_path), exist_ok=True)

    # Khởi tạo bảng table
    table = {}

    # Kiểm tra nếu file table.json tồn tại thì đọc nội dung
    if os.path.exists(table_path):
        with open(table_path, 'r') as f:  # Đọc bảng table từ file
            table = json.load(f)

    # Cập nhật bảng với hash mới và đường dẫn mới
    table[hash] = metadata['path']

    # Lưu lại bảng vào file table.json
    with open(table_path, 'w') as f2:  # Mở lại file để ghi
        json.dump(table, f2, indent=4)
        
    send("",f"CONFIRM :{hash}")
    

def main():
    # Tạo folder ứng với peer
    print(f'{CLIENT} is on')
    create_folder(CLIENT)
    
    # Chạy chọn port listen cho peer
    port = readatline(f"{CLIENT}/peer_id.txt",3)
    host = readatline(f"{CLIENT}/peer_id.txt",2)
    print(port)
    if port == "": port = random.randint(6000, 7000)
    else: port = int(port)
    while not bind_port('localhost', port): port = random.randint(6000, 7000)
    global PORT
    PORT = port
    print(f"Bound to listen port {PORT}")
    
    # Chạy thread listen các request
    threading.Thread(target=listen_for_peers, args=()).start()
    
    # Đọc metadata từ file JSON
    metadata = read_metadata("meta_info.json")
    print(metadata)

    # Phân tích URL từ announce
    announce_url = metadata["announce"]
    SER_IP, SER_PORT = parse_announce_url(announce_url)
    print(SER_IP, SER_PORT)
    
    # Kết nối với tracker
    SOCKET.connect((SER_IP, SER_PORT))
    while True:
        command = input(">> ")
        match command:
            case "read":
                
            case "res": register(TRACKER_URL)
            case "upload":
                print(upload(TRACKER_URL, input(f'Nhập đường dẫn file: ')))
            case "end": 
                stop()
                break
            case "req": 
                hash = input("Nhập hashinfo: ")
                request(hash, metadata)
            case "test": print(PORT)
            case _: print("ERROR COMMAND")
    SOCKET.close()
            
    
if __name__ == "__main__":
    main()