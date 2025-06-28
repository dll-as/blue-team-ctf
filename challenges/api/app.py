from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import re
import datetime
import logging
from logging.handlers import RotatingFileHandler

app = Flask(__name__)

# limiting request 60 per meinut for only ip
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["60 per minute"]  # 60 درخواست در دقیقه برای هر IP
)

# log system
logging.basicConfig(level=logging.INFO)
handler = RotatingFileHandler('api_requests.log', maxBytes=10000, backupCount=3)
handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
app.logger.addHandler(handler)

def log_request(response):
    """save the log requests"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    client_ip = request.remote_addr
    method = request.method
    path = request.path
    user_agent = request.headers.get('User-Agent', 'N/A')
    status_code = response.status_code
    
    log_message = f"{timestamp} - IP: {client_ip} - {method} {path} - Status: {status_code} - UA: {user_agent}"
    
    # 
    if method == 'POST' and request.content_type == 'application/json':
        try:
            data = request.get_json()
            log_message += f" - Data: {data}"
        except:
            log_message += " - Data: Invalid JSON"
    
    app.logger.info(log_message)
    return response

app.after_request(log_request)

def detect_command_injection(input_data):
    """un utilize command injection system"""
    if isinstance(input_data, dict):
        for key, value in input_data.items():
            if detect_command_injection(value):
                return True
        return False
    elif isinstance(input_data, (list, tuple)):
        for item in input_data:
            if detect_command_injection(item):
                return True
        return False
    elif isinstance(input_data, str):
        # Command Injection not valid digits
        patterns = [
            r'[\|\&\;]',  # digits of pipe, ampersand, semicolon
            r'\b(rm|wget|curl|bash|sh|python|perl|php)\b',
            r'\$(?:\{|\().*?(?:\}|\))',  # ${command} or $(command)
            r'`.*?`'  # command in backticks
        ]
        
        for pattern in patterns:
            if re.search(pattern, input_data, re.IGNORECASE):
                return True
    return False

@app.route('/blue_team_system', methods=['POST'])
@limiter.limit("60 per minute")  # submit limits
def receive_data():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # check Command Injection
        if detect_command_injection(data):
            app.logger.warning(f"Command injection attempt detected from IP: {request.remote_addr}")
            return jsonify({"error": "Invalid input detected"}), 400
        
        
        return jsonify({"message": "Data received successfully", "data": data}), 200
    
    except Exception as e:
        app.logger.error(f"Error processing request: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(debug=True)
