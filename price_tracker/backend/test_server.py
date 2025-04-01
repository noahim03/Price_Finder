from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/test', methods=['GET'])
def test():
    return jsonify({"message": "Test server is working!"})

if __name__ == '__main__':
    app.run(port=3001, debug=True) 