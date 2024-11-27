import threading
from flask import Flask, request, jsonify
import uuid
import socket
import json
import hashlib
import os
import requests

PORT = 0

app = Flask(__name__)
# thread_local = threading.local()
active_peers = []

@app.route('/register', methods=['POST'])
def register():
    peer_id = str(uuid.uuid4())  # Khởi tạo peer_id nếu chưa có
    data = request.json  # Lấy JSON từ request gồm ip và port
    data['id'] = peer_id
    data['ip'] = data['ip']
    with open(f'tracker/peers/{peer_id}.json', 'w') as f: json.dump(data, f, indent=4)
    
    active_peers.append(peer_id)
    
    return jsonify({
        "message": "Register successfully",
        "id" : peer_id,
    }), 200

@app.route('/login', methods=['POST'])
def login():
    data = request.json  # Lấy JSON từ request gồm id, ip, port
    
    print(data)
    peer_id = data['id']
    data['ip'] = data['ip']
    
    peer_path = f"tracker/peers/{data['id']}.json"
    print(peer_path)
    if not os.path.exists(peer_path): 
        # conn.send("Login Failed".encode()) 
        return jsonify( {"message": "Login Failed"} ), 200
    else: 
        with open(f'{peer_path}', 'r') as f:
            peer = json.load(f)
            if  peer['port'] != data['port'] or peer['ip'] != data['ip'] :
                peer['port']    = int(data['port'])
                peer['ip']      = data['ip']
                with open(f'{peer_path}', 'w') as f: json.dump(peer, f, indent=4)
        # thread_local.login = True
        
        active_peers.append(peer_id)
        # conn.send("Login Successfully".encode())
        return jsonify({
            "message": "Login successfully!",
            "id": peer_id
            }), 200

@app.route('/logout', methods=['POST'])
def logout():
    data = request.json  # Lấy JSON từ request gồm id
    peer_id = data.get('id')
    
    if not peer_id:
        return jsonify({"message": "Peer ID is required"}), 400
    
    # Kiểm tra nếu peer tồn tại trong danh sách `active_peers`
    if peer_id in active_peers:
        active_peers.remove(peer_id)
        return jsonify({"message": "Logout successful"}), 200
    else:
        return jsonify({"message": "Peer ID not found or already logged out"}), 404

@app.route('/request', methods=['GET'])
def peerlist():
    data = request.json
    hash = data.get('info')
    peer_id = data.get('id')
    
    if not peer_id in active_peers:
        return jsonify({
            "message": "Need to login"
        }), 404
    
    if not os.path.exists(f'tracker/metainfo/{hash}.json'): 
        return jsonify({"message": "Error hashinfo"}), 404
    
    with open(f'tracker/info_peer/{hash}.json', 'r') as f2: 
        peerlist = (json.load(f2))['peers']
    peerset = set(peerlist)
    activepeerlist = list(peerset & set(active_peers)) # tạo mảng chứa các peer active
    if peer_id in activepeerlist: activepeerlist.remove(peer_id)
    print(activepeerlist)
    jsonres= []
    for peer in activepeerlist:
        with open(f'tracker/peers/{peer}.json', 'r') as f: 
            jsonres.append(json.load(f))
    return jsonify({
        "message": "Request ok",
        "data": jsonres
    }), 200

@app.route('/upload', methods=['POST'])
def upload():
    data = request.json
    peer_id = data.get('id')
    
    if not peer_id in active_peers:
        return jsonify({
            "message": "Need to login"
        }), 404
        
    tmpobj = {} 
    tmpobj['info'] = data['info']
    arr=[]
    arr.append(peer_id)
    tmpobj['peers'] = arr
    with open(f'tracker/info_peer/{tmpobj["info"]}.json', 'w') as f: json.dump(tmpobj, f, indent=4) 
    data.pop('id', None) 
    with open(f'tracker/metainfo/{tmpobj["info"]}.json', 'w') as f: json.dump(data, f, indent=4) 
    return jsonify({
        "message": "Upload ok",
        "data": data
    }), 200

if __name__ == '__main__':
    app.run( debug=True, host='localhost', port=5000 )  # Chạy Flask trên cổng 5000
