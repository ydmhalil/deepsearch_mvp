from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins=['http://localhost:5173', 'http://localhost:5000', 'http://localhost:5001'])

@app.route('/')
def home():
    return jsonify({'message': 'Test server working'})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    return jsonify({
        'success': True,
        'message': 'Login test successful',
        'received': data
    })

if __name__ == '__main__':
    print("🚀 Starting Test Server...")
    app.run(host='0.0.0.0', port=5002, debug=True)