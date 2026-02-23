# AI Based VLSI Circuit Fault Detection Implementation Plan

## Overview
This document outlines the step-by-step implementation plan for an AI-powered intelligent fault detection backend. It processes an image URL of a VLSI layout, performs anomaly detection using a pre-trained Autoencoder, classifies the fault (if any) using a CNN, and serves the results via a RESTful Flask API.

## Phase 1: Environment & Project Setup
1. **Virtual Environment Setup**: Create an isolated Python environment to manage dependencies securely.
2. **Library Installation**: Install the required Python packages:
   - `Flask`, `flask-cors` (for backend REST API and Cross-Origin communication).
   - `tensorflow`, `keras` (for Deep Learning models).
   - `opencv-python`, `numpy` (for image processing).
   - `requests` (to fetch layout images from URLs).
3. **Directory Structure**:
   ```
   vlsi-fault-detection/
   ├── app.py                 # Main Flask application entry point
   ├── requirements.txt       # Dependencies
   ├── models/                # Directory to store .h5 models
   │   ├── autoencoder.h5     # Pre-trained Autoencoder
   │   └── cnn_classifier.h5  # Pre-trained CNN for fault classification
   └── utils/                 # Helper functions
       ├── image_utils.py     # Image fetching and preprocessing
       └── inference.py       # Functions to interact with Keras models
   ```

## Phase 2: Image Processing Utilities (`utils/image_utils.py`)
1. **Image Retrieval Logic**: Use the `requests` library to fetch the image object securely from the URL provided by the frontend.
2. **Preprocessing Pipeline**: Implement OpenCV-based transforms according to exact system specifications:
   - Open image and convert to **grayscale**.
   - **Resize** strictly to `128x128`.
   - **Normalize** pixel values by dividing by 255.0 to bring values between `0` and `1`.
   - Expand dimensions to fit Keras input formats (e.g., `(1, 128, 128, 1)`).

## Phase 3: AI Inference Engine (`utils/inference.py`)
1. **Model Loading On Startup**: Load the `.h5` models directly when the server starts to avoid latency on API requests.
2. **Anomaly Detection (Autoencoder)**:
   - Feed the preprocessed image into the autoencoder to get a reconstructed image.
   - Calculate Reconstruction Loss via Mean Squared Error (MSE).
   - Define a `RECONSTRUCTION_THRESHOLD`.
   - If `MSE > Threshold` -> Fault Detected.
   - If `MSE <= Threshold` -> Fault-Free.
3. **Fault Classification (CNN)**:
   - If a fault is detected, feed the same preprocessed image to the CNN classifier.
   - Extract the highest probability prediction.
   - Map exactly to: `Stuck-at Fault`, `Bridging Fault`, `Open Circuit Fault`, or `Delay Fault`.

## Phase 4: API Development (`app.py`)
1. **Initialize API**: Setup the core Flask app and allow CORS so the website frontend can interface seamlessly.
2. **POST Endpoint (`/detectFault`)**:
   - Extract `image_url` strictly from the JSON input.
   - Pass URL to the preprocessing engine.
   - Await anomaly detection results.
   - Format results into the expected JSON response contract:
     ```json
     {
        "fault_status": "Detected", // or "Not Detected"
        "fault_type": "Bridging Fault", // or null if not detected
        "probability": 0.87,
        "reconstruction_loss": 0.034
     }
     ```

## Phase 5: Error Handling & Robustness
1. Return gracefully generated JSON errors (Status `400` or `500`) for:
   - Missing URL from frontend submission.
   - Broken URLs or un-fetchable images (404/403 errors).
   - Models not found or failing inference due to bad input shapes.

## Phase 6: Frontend Integration Guidelines (Dashboard)
To seamlessly integrate with your existing website:
1. Make a Javascript `fetch` or `axios` POST request to `/detectFault`.
2. Map the response explicitly onto the dashboard elements:
   - If `fault_status == "Detected"`, trigger a "highlight message" on the UI visually cautioning the user.
   - Populate specific UI tags for **Fault Type**, **Probability Score**, and **Circuit Health Status**.
