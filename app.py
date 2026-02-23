import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from utils.image_utils import fetch_and_preprocess_image
from utils.inference import load_models, detect_anomaly, classify_fault, optimize_layout

app = Flask(__name__)

# Enable CORS for frontend communication
CORS(app)

# Load autoencoder.h5 and cnn_classifier.h5 on startup
load_models()

@app.route('/', methods=['GET'])
def index():
    return jsonify({
        "status": "AI VLSI Fault Detection API is running",
        "documentation": "Send a POST request to /detectFault with {'image_url': 'URL_STRING'} or Base64 encoded 'data:image/...'"
    })

@app.route('/status', methods=['GET'])
def status():
    return jsonify({
        "status": "online",
        "message": "Backend is reachable"
    }), 200

@app.route('/detectFault', methods=['GET', 'POST'])
def detect_fault():
    if request.method == 'GET':
        return jsonify({
            "error": "Method Not Allowed",
            "message": "You are making a GET request (e.g., from a web browser). This endpoint requires a POST request.",
            "expected_body": {"image_url": "string"}
        }), 405

    # Parse JSON body
    data = request.get_json(silent=True)
    
    # Step 5: Error Handling - Missing image_url
    if not data or 'image_url' not in data:
        return jsonify({"error": "image_url is required in the JSON body."}), 400
        
    image_url = data.get('image_url')
    if not isinstance(image_url, str) or not image_url.strip():
        return jsonify({"error": "image_url must be a valid non-empty string."}), 400
        
    try:
        # Step 4: Preprocess image
        preprocessed_image = fetch_and_preprocess_image(image_url)
        
        # Step 4: Detect anomaly using autoencoder
        fault_detected, reconstruction_loss = detect_anomaly(preprocessed_image)
        
        # Format metrics to be more readable
        reconstruction_loss = round(reconstruction_loss, 4)
        
        if fault_detected:
            # Step 4: Classify fault
            fault_type, probability = classify_fault(preprocessed_image)
            
            # RL Layout Optimization
            rl_optimization = optimize_layout(fault_type, reconstruction_loss, probability)
            
            return jsonify({
                "fault_status": "Detected",
                "fault_type": fault_type,
                "probability": round(probability, 4),
                "reconstruction_loss": reconstruction_loss,
                "layout_optimization": rl_optimization["optimization_suggestion"],
                "optimization_score": rl_optimization["optimization_score"]
            }), 200
        else:
            return jsonify({
                "fault_status": "Not Detected",
                "fault_type": None,
                "probability": 0.0,
                "reconstruction_loss": reconstruction_loss,
                "layout_optimization": "Layout is optimal.",
                "optimization_score": 0.0
            }), 200
            
    except Exception as e:
        # Step 5: Error Handling - image not fetchable or inference fails
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Initialize models directory if it doesn't exist
    os.makedirs('models', exist_ok=True)
    
    # Run on port 5000
    app.run(host='0.0.0.0', port=5000, debug=True)
