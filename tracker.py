import socket
import threading
import json
import hashlib
import uuid
import os
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)
@app.route('/hello', methods=['GET'])
def hello():
    return "Hello, world!", 200

@app.route('/data', methods=['POST'])
def receive_data():
    data = request.json  # Lấy JSON từ request
    print(f"Received JSON data: {data}")
    return jsonify({"message": "Data received!"}), 200

active_peers = []
CHUNKSIZE = 512*1024
SERVER = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
flag = True


def handle_client(conn, addr): 
    ip, port = addr 
    login = False 
    peer_id = None 
    global flag
    while flag: 
        try: 
            data = b''
            while flag:
                part = conn.recv(CHUNKSIZE)
                if not part:  # Nếu không còn dữ liệu để nhận, thoát vòng lặp
                    break
                data += part
                if b'\n' or b'}' in part:  # Kiểm tra ký tự kết thúc
                    break
            data = data.decode() 
            print(data)
            if data.startswith("REGISTER"): # REGISTER IP:localhost PORT:1123
                peer_id = str(uuid.uuid4()) 
                # Tạo file json peer
                msg = data
                msg = msg.split(":")
                msg[1] = msg[1].split(" ")[0]
                
                peerobj = {} 
                peerobj['id'] = peer_id 
                peerobj['ip'] = msg[1][:-1]
                peerobj['port'] = int(msg[2])
                with open(f'tracker/peers/{peer_id}.json', 'w') as f: json.dump(peerobj, f, indent=4)
                login = True 
                
                # Gửi lại thông điệp cho peer
                conn.send((f"Registered Successfully with id:{peer_id}").encode()) 
                conn.send(peer_id.encode()) # trả id về 
            elif data.startswith("LOGIN"): # LOGIN id:abcxyz ip:localhost port:12345                
                # Lấy dữ liệu
                msg = data.split(":")
                msg[1] = msg[1].split(" ")[0] #ID
                msg[2] = (msg[2].split(" ")[0])[:-1] #IP
                peer_id = msg[1][:-1]
                
                peer_path = f'tracker/peers/{peer_id}.json'
                print(peer_path)
                if not os.path.exists(peer_path): 
                    conn.send("Login Failed".encode()) 
                else: 
                    with open(f'{peer_path}', 'r') as f: 
                        peer = json.load(f)
                        if peer['port'] != msg[3] or peer['ip'] != msg[2] :
                            peer['port'] = int(msg[3])
                            peer['ip'] = msg[2]
                            with open(f'{peer_path}', 'w') as f: json.dump(peer, f, indent=4)
                    login = True
                    active_peers.append(peer_id)
                    conn.send("Login Successfully".encode())
            elif data.startswith("STOP"):
                active_peers.remove(peer_id)
                login = False
                break 
            elif not login: conn.send("Need to login".encode()) 
            elif login and data.startswith("{"): # upload gồm path, size, count, pieces 
                hashdata = hashlib.sha1(data.encode()).hexdigest() # hash các thông tin đó 
                data = json.loads(data) # đọc như json 
                data['info'] = hashdata # gán cho trường info 
                arr=[]
                tmpobj = {} 
                tmpobj['info'] = data['info']
                arr.append(peer_id)
                tmpobj['peers'] = arr
                with open(f'tracker/info_peer/{tmpobj['info']}.json', 'w') as f: json.dump(tmpobj, f, indent=4)  
                with open(f'tracker/metainfo/{hashdata}.json', 'w') as f: json.dump(data, f, indent=4) 
                conn.send(json.dumps(data).encode()) 
            elif login and data.startswith("REQUEST"): # download REQUEST :abcxyz
                print("Request") # _, piece_id = data.split(" ") 
                index = data.index(':') + 1 
                name = data[index:].strip() # filename của
                if not os.path.exists(f'tracker/metainfo/{name}.json'): 
                    conn.sendall(json.dumps("Error hashinfo").encode())
                    break
                with open(f'tracker/info_peer/{name}.json', 'r') as f2: 
                    peerlist = (json.load(f2))['peers']
                peerset = set(peerlist)
                print(peerset)
                activepeerlist = list(peerset & set(active_peers)) # tạo mảng chứa các peer active
                print(active_peers)
                print(activepeerlist)
                if peer_id in activepeerlist: activepeerlist.remove(peer_id)
                print(activepeerlist)
                jsonres= []
                for peer in activepeerlist:
                    with open(f'tracker/peers/{peer}.json', 'r') as f: 
                        jsonres.append(json.load(f))
                
                conn.sendall(json.dumps(jsonres).encode())
            elif login and data.startswith("CONFIRM"): #  CONFIRM :abcxyz  sẽ gửi khi peer load xong
                print("Confirm")
                index = data.index(':') + 1 
                info = data[index:].strip()
                with open(f'tracker/info_peer/{info}.json', 'r') as f2: 
                    peerlist = json.load(f2)
                peer = peerlist['peers']
                peer.append(peer_id)
                peerlist['peers'] = peer
                with open(f'tracker/info_peer/{peerlist['info']}.json', 'w') as f: json.dump(peerlist, f, indent=4) 
            else: print("Error command") 
        except json.JSONDecodeError as e: print(f"Invalid JSON data: {e}") 
        except Exception as e: print(f"An error occurred: {e}") 
    flag = False
    conn.close()

def listen():
    SERVER.bind(('localhost', 5000))
    SERVER.listen()
    print("[TRACKER] Server started...")
    global flag
    while flag:
        conn, addr = SERVER.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()

# Khởi động server tracker
def start_tracker():
    t = threading.Thread(target=listen, args=())
    t.start()
    if input().strip().upper() == "end":
        global flag
        flag = False
    t.join()

if __name__ == "__main__":
    start_tracker()