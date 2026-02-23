import cv2
import numpy as np
import requests
import base64

def fetch_and_preprocess_image(image_url):
    try:
        if image_url.startswith('data:'):
            # Extract base64 data and fix any padding issues
            base64_data = image_url.split(',')[1]
            # Fix incorrect padding: add missing '=' signs to make length a multiple of 4
            missing_padding = len(base64_data) % 4
            if missing_padding:
                base64_data += '=' * (4 - missing_padding)
            image_bytes = base64.b64decode(base64_data)
            image_array = np.asarray(bytearray(image_bytes), dtype=np.uint8)
        else:
            # Fetch image from URL with a standard User-Agent header to avoid 403 Forbidden errors
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(image_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Convert response content to numpy array
            image_array = np.asarray(bytearray(response.content), dtype=np.uint8)
        
        # Decode image using OpenCV
        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError("Failed to decode image from URL.")
            
        # Convert to grayscale
        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Resize image to exactly 128x128
        resized_image = cv2.resize(gray_image, (128, 128))
        
        # Normalize pixel values to range [0, 1]
        normalized_image = resized_image / 255.0
        
        # Reshape to (1, 128, 128, 1) for model input
        model_input = np.reshape(normalized_image, (1, 128, 128, 1))
        
        return model_input
        
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to fetch image: {str(e)}")
    except Exception as e:
        raise Exception(f"Error during image processing: {str(e)}")
