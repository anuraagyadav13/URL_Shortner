import os
import numpy as np
import scipy.stats as stats
from tensorflow.keras.models import load_model

# Constants
THRESHOLD = 0.035
FAULT_CLASSES = {
    0: "Stuck-at Fault",
    1: "Bridging Fault",
    2: "Open Circuit Fault",
    3: "Delay Fault"
}

autoencoder_model = None
cnn_classifier_model = None

def load_models():
    """
    Loads autoencoder and CNN classifier models on startup.
    Assumes models are stored in a 'models' directory.
    """
    global autoencoder_model, cnn_classifier_model
    
    # Define paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    autoencoder_path = os.path.join(base_dir, 'Models', 'autoencoder.h5')
    cnn_path = os.path.join(base_dir, 'Models', 'cnn_classifier.h5')
    
    try:
        # We wrap loading in try-except because the actual model files 
        # might not exist yet during initial setup.
        if os.path.exists(autoencoder_path):
            autoencoder_model = load_model(autoencoder_path, compile=False)
            print("Autoencoder model loaded successfully.")
        else:
            print(f"Warning: Autoencoder model not found at {autoencoder_path}")
            
        if os.path.exists(cnn_path):
            cnn_classifier_model = load_model(cnn_path, compile=False)
            print("CNN Classifier model loaded successfully.")
        else:
            print(f"Warning: CNN Classifier model not found at {cnn_path}")
            
    except Exception as e:
        print(f"Error loading models: {str(e)}")

def detect_anomaly(image_array):
    """
    Passes image through autoencoder, calculates MSE, and compares with threshold.
    """
    global autoencoder_model, cnn_classifier_model
    if autoencoder_model is None or cnn_classifier_model is None:
        load_models()
        
    if autoencoder_model is None:
        raise Exception("Autoencoder model is not loaded.")
        
    # Pass image through encoder-decoder
    reconstructed = autoencoder_model.predict(image_array, verbose=0)
    
    # Calculate reconstruction loss using Mean Squared Error
    mse = np.mean(np.square(image_array - reconstructed))
    
    # Compare with threshold
    fault_detected = bool(mse > THRESHOLD)
    
    return fault_detected, float(mse)

def classify_fault(image_array):
    """
    Classifies the fault using CNN classifier.
    """
    if cnn_classifier_model is None:
        raise Exception("CNN Classifier model is not loaded.")
        
    predictions = cnn_classifier_model.predict(image_array, verbose=0)[0]
    
    predicted_class_idx = int(np.argmax(predictions))
    probability = float(predictions[predicted_class_idx])
    
    # ENTROPY CHECK
    entropy = stats.entropy(predictions)
    
    # Low entropy = confident prediction
    # High entropy = unsure prediction
    if probability < 0.80 or entropy > 1.0:
        fault_type = "Uncertain Fault Pattern"
    else:
        fault_type = FAULT_CLASSES.get(predicted_class_idx, "Unknown Fault")
    
    return fault_type, probability

def optimize_layout(fault_type, reconstruction_loss, probability):
    """
    Simulates an RL agent providing layout optimization suggestions.
    Higher reconstruction loss results in a higher urgency score.
    """
    if fault_type == "Unknown Pattern" or fault_type == "Unknown Fault":
        return {
            "optimization_suggestion": "Pattern not recognized. Manual inspection required.",
            "optimization_score": 0.0
        }
        
    # Base score calculated using loss and confidence
    # Loss is typically a small decimal, so we scale it up
    urgency_base = min((reconstruction_loss * 50) + (probability * 20), 100.0)
    score = round(urgency_base, 2)
    
    suggestion = ""
    
    if fault_type == "Delay Fault":
        suggestion = "Reduce interconnect length or improve clock routing."
    elif fault_type == "Bridging Fault":
        suggestion = "Increase spacing between metal lines."
    elif fault_type == "Open Circuit Fault":
        suggestion = "Improve via connectivity or routing path."
    elif fault_type == "Stuck-at Fault":
        suggestion = "Add redundancy or improve logic gate placement."
        
    return {
        "optimization_suggestion": suggestion,
        "optimization_score": score
    }
