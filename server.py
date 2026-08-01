"""
第六届"红星杯" — 共享任务看板服务器
启动方式: python server.py
访问地址: http://你的IP:5050

密码保护: 默认密码 hongxingbei2026
可通过环境变量 PASSWORD 自定义
"""
import json
import os
import hashlib
import threading
import secrets
from functools import wraps
from flask import Flask, request, jsonify, send_file, make_response

app = Flask(__name__)

# 密钥 & 密码
SECRET_KEY = os.environ.get('SECRET_KEY', secrets.token_hex(32))
PASSWORD = os.environ.get('PASSWORD', 'hongxingbei2026')
app.secret_key = SECRET_KEY

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tasks_data.json')
LOCK = threading.Lock()
HTML_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '红星杯时间线.html')

# Token: sha256(timestamp + secret + password) 对，用作登录凭证
def make_token():
    import time
    raw = f"{time.time()}:{SECRET_KEY}:{PASSWORD}"
    return hashlib.sha256(raw.encode()).hexdigest()


def check_token(token):
    return token == make_token()


def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def save_data(data):
    with LOCK:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


# ==================== 鉴权装饰器 ====================

def require_auth(f):
    """检查 cookie 中的 token 是否有效"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = request.cookies.get('hxb_token', '')
        if not token or not check_token(token):
            return jsonify({'error': '未登录', 'need_auth': True}), 401
        return f(*args, **kwargs)
    return wrapper


# ==================== 路由 ====================

@app.route('/')
def index():
    return send_file(HTML_FILE)


@app.route('/api/login', methods=['POST'])
def login():
    """验证密码，返回 token"""
    body = request.get_json(force=True)
    pwd = body.get('password', '')
    if pwd != PASSWORD:
        # 简单防暴力破解：延迟响应
        import time; time.sleep(1)
        return jsonify({'ok': False, 'msg': '密码错误'}), 403

    token = make_token()
    resp = make_response(jsonify({'ok': True, 'token': token}))
    resp.set_cookie('hxb_token', token,
                    max_age=60*60*24*30,  # 30天
                    httponly=True,
                    samesite='Lax',
                    secure=False)
    return resp


@app.route('/api/check', methods=['GET'])
def check_auth():
    """检查是否已登录"""
    token = request.cookies.get('hxb_token', '')
    if token and check_token(token):
        return jsonify({'ok': True})
    return jsonify({'ok': False}), 401


@app.route('/api/tasks', methods=['GET'])
@require_auth
def get_tasks():
    return jsonify(load_data())


@app.route('/api/tasks', methods=['POST'])
@require_auth
def update_task():
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
@require_auth
def reset_tasks():
    save_data({})
    return jsonify({'ok': True})


@app.route('/api/import', methods=['POST'])
@require_auth
def import_local():
    body = request.get_json(force=True)
    incoming = body.get('tasks', {})
    if not isinstance(incoming, dict):
        return jsonify({'error': 'tasks 应为字典'}), 400

    data = load_data()
    merged = 0
    for key, entry in incoming.items():
        if key not in data:
            data[key] = entry
            merged += 1
    save_data(data)
    return jsonify({'ok': True, 'imported': merged})


if __name__ == '__main__':
    print('=' * 50)
    print('  第六届"红星杯" · 共享任务看板')
    print('=' * 50)
    print()
    print(f'  访问密码: {PASSWORD}')
    print()
    print('  本机访问: http://localhost:5050')
    print()
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('10.254.254.254', 1))
        ip = s.getsockname()[0]
        s.close()
        print(f'  局域网访问: http://{ip}:5050')
    except Exception:
        pass
    print()
    print('  按 Ctrl+C 停止服务器')
    print('=' * 50)

    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5050)), debug=False)
