import threading
import time
import socket
import webview
from app import app

def find_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('127.0.0.1', 0))
    port = s.getsockname()[1]
    s.close()
    return port

def run_flask(port):
    app.run(host='127.0.0.1', port=port, debug=False, use_reloader=False)

def main():
    port = find_free_port()
    t = threading.Thread(target=run_flask, args=(port,), daemon=True)
    t.start()

    # Wait for server to boot
    time.sleep(1.2)

    url = f"http://127.0.0.1:{port}"
    print(f"[*] 窩在家桌面應用程式啟動中: {url}")

    webview.create_window(
        title="窩在家包租代管 ｜ 企業級形象官網暨智慧詢價管理系統",
        url=url,
        width=1320,
        height=880,
        min_size=(980, 680),
        text_select=True,
        zoomable=True
    )
    webview.start()

if __name__ == '__main__':
    main()

