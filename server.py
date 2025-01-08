import asyncio
import json, util
from websockets.asyncio.server import serve
VAP_HOST = "localhost"
VAP_PORT = 50008

_connected_clients = set()

async def ini_connect(websocket):
    _connected_clients.add(websocket)
    try:
        print(f"Client connected: {websocket.remote_address}")  # クライアントの接続情報を表示
        await websocket.wait_closed()                           # クライアントの接続が閉じるまで待機
    finally:
        print(f"Client disconnected: {websocket.remote_address}") # クライアントの切断情報を表示
        _connected_clients.discard(websocket)                     # クライアントを接続中リストから削除

async def vap_module():
    global VAP_HOST, VAP_PORT, _vap_future
    
    reader, writer = await asyncio.open_connection(VAP_HOST, VAP_PORT)
    
    try:
        n = 0
        while True:
            data_size = await reader.readexactly(4)             # 4バイトのデータサイズを受信
            size = int.from_bytes(data_size, 'little')          # バイト列を整数に変換
            data = await reader.readexactly(size)               # データを受信
            vap_result = util.conv_bytearray_2_vapresult(data)  # バイト列をVAPResultに変換
            
            _vap_future = vap_result['p_future'][1]                # 相手の終話予測結果を取得
            
            n += 1
            if n > 20:
                n = 0
                print(_vap_future)
                
            if _connected_clients:                                      # クライアントが接続中の場合
                message = json.dumps({"vap_future": f"{_vap_future}"})  # メッセージを作成
                disconnected_clients = []                               # 切断されたクライアントを記録するリスト
                for websocket in _connected_clients:                    # 接続中のクライアントにメッセージを送信
                    try:
                        await websocket.send(message)                   # データを送信
                    except Exception:
                        disconnected_clients.append(websocket)          # 切断されたクライアントを記録
                
                for websocket in disconnected_clients:                  # 切断されたクライアントを接続中リストから削除
                    _connected_clients.discard(websocket)               # クライアントを接続中リストから削除
                    
    except asyncio.IncompleteReadError:
        print('Disconnected from the server: IncompleteReadError')
    except Exception as e:
        print('Disconnected from the server')
        print(e)
    finally:
        writer.close()
        await writer.wait_closed()
        
async def main():
    server = serve(ini_connect, "0.0.0.0", 8765)
    await asyncio.gather(server, vap_module())

if __name__ == "__main__":
    asyncio.run(main())

