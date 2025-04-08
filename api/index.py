from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return "<h1>Welcome to the Greeting API</h1><p>Use the <code>/greet</code> endpoint to get a greeting message.</p><p>For API documentation, visit <a href='/api-docs'>/api-docs</a>.</p>"

@app.route('/greet', methods=['GET'])
def greet():
    
    name = request.args.get('name')
    
    if name:
        return jsonify({"message": f"Hi, {name}!"})
    else:
        return jsonify({"error": "Please specify a name in the 'name' query parameter."}), 400

@app.route('/api-docs', methods=['GET'])
def api_docs():
    return '''
    <h1>API Documentation</h1>
    <h2>Endpoints</h2>
    <h3>GET /</h3>
    <p>The home endpoint. Returns a welcome message and links to the API documentation.</p>
    <h3>GET /greet</h3>
    <p>Returns a greeting message.</p>
    <p><strong>Query Parameters:</strong></p>
    <ul>
        <li><code>name</code> (required): The name of the person to greet.</li>
    </ul>
    <p><strong>Responses:</strong></p>
    <ul>
        <li>200: A JSON object with the greeting message.</li>
        <li>400: A JSON object with an error message if the 'name' query parameter is not provided.</li>
    </ul>
    '''

if __name__=='__main__':
    app.run(debug=True)
