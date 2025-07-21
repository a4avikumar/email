from flask import Flask, request, jsonify
from validator import validate_email_address_custom

app = Flask(__name__)

@app.route("/validate_email", methods=["POST"])
def validate_email():
    data = request.get_json()
    if not data or 'email' not in data:
        return jsonify({"error": "Email field required"}), 400
    result = validate_email_address_custom(data['email'])
    return jsonify(result)

# Vercel will look for "app" variable!
