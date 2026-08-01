"""
第六届"红星杯" — 共享任务看板服务器
启动方式: python server.py
访问地址: http://你的IP:5050
"""
import json
import os
import threading
from flask import Flask, request, jsonify, send_file

app = Flask(__name__)
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tasks_data.json')
LOCK = threading.Lock()

HTML_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '红星杯时间线.html')


def load_data():
    """读取任务数据，文件不存在则返回空字典"""
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def save_data(data):
    """写入任务数据（线程安全）"""
    with LOCK:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


# ==================== 路由 ====================

@app.route('/')
def index():
    """直接返回 HTML 页面"""
    return send_file(HTML_FILE)


@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    """获取全部任务状态"""
    return jsonify(load_data())


@app.route('/api/tasks', methods=['POST'])
def update_task():
    """更新单个任务 {key: str, done: bool, owner: str}"""
    body = request.get_json(force=True)
    key = body.get('key', '').strip()
    if not key:
        return jsonify({'error': '缺少 key'}), 400

    data = load_data()
    entry = data.get(key, {})
    if 'done' in body:
        entry['done'] = bool(body['done'])
    if 'owner' in body:
        entry['owner'] = str(body.get('owner', '')).strip()
    data[key] = entry
    save_data(data)
    return jsonify({'ok': True, 'key': key, 'entry': entry})


@app.route('/api/reset', methods=['POST'])
def reset_tasks():
    """清空全部任务数据"""
    save_data({})
    return jsonify({'ok': True})


@app.route('/api/import', methods=['POST'])
def import_local():
    """从本地 localStorage 批量导入（合并模式：服务器已有的不覆盖）"""
    body = request.get_json(force=True)
    incoming = body.get('tasks', {})
    if not isinstance(incoming, dict):
        return jsonify({'error': 'tasks 应为字典'}), 400

    data = load_data()
    merged = 0
    for key, entry in incoming.items():
        if key not in data:  # 服务器没有的才导入
            data[key] = entry
            merged += 1
    save_data(data)
    return jsonify({'ok': True, 'imported': merged})


if __name__ == '__main__':
    print('=' * 50)
    print('  第六届"红星杯" · 共享任务看板')
    print('=' * 50)
    print()
    print('  本机访问: http://localhost:5050')
    print()
    # 尝试获取本机局域网 IP
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('10.254.254.254', 1))
        ip = s.getsockname()[0]
        s.close()
        print(f'  局域网访问: http://{ip}:5050')
        print()
        print('  👆 把这个地址发给同事即可共享看板')
    except Exception:
        print('  (无法自动获取局域网 IP，请手动查看)')
    print()
    print('  按 Ctrl+C 停止服务器')
    print('=' * 50)

    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5050)), debug=False)
