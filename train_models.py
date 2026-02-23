import os
import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models

def generate_synthetic_data(num_samples=100, is_faulty=False):
    """
    Generates synthetic 128x128 grayscale images representing VLSI circuits.
    In a real scenario, you would load your actual dataset using cv2 or tf.data.
    """
    print(f"Generating {num_samples} synthetic samples (Faulty={is_faulty})...")
    # Base pattern (random noise representing a complex circuit)
    data = np.random.rand(num_samples, 128, 128, 1) * 0.5
    
    labels = []
    
    for i in range(num_samples):
        if is_faulty:
            # Introduce random faults
            fault_type = np.random.randint(0, 4) # 0 to 3
            labels.append(fault_type)
            
            if fault_type == 0: # Stuck-at Fault: bright spots
                data[i, 10:20, 10:20, 0] = 1.0
            elif fault_type == 1: # Bridging Fault: thick lines connecting lines
                data[i, 50:70, 50:55, 0] = 1.0
            elif fault_type == 2: # Open Circuit Fault: broken lines (dark spots)
                data[i, 80:90, 80:90, 0] = 0.0
            elif fault_type == 3: # Delay Fault: blurry areas
                pass # Already random enough for synthetic classification
        else:
            # Add some normal "circuit" lines
            data[i, 20:100, 30:35, 0] = 0.8
            data[i, 40:45, 10:90, 0] = 0.8
            
    return data, np.array(labels) if is_faulty else None

def build_and_train_autoencoder():
    print("\n--- Building and Training Autoencoder ---")
    
    # 1. Generate normal circuit data for Autoencoder
    x_train, _ = generate_synthetic_data(num_samples=500, is_faulty=False)
    x_val, _ = generate_synthetic_data(num_samples=100, is_faulty=False)
    
    # 2. Define Autoencoder Architecture
    input_img = layers.Input(shape=(128, 128, 1))
    
    # Encoder
    x = layers.Conv2D(32, (3, 3), activation='relu', padding='same')(input_img)
    x = layers.MaxPooling2D((2, 2), padding='same')(x)
    x = layers.Conv2D(16, (3, 3), activation='relu', padding='same')(x)
    encoded = layers.MaxPooling2D((2, 2), padding='same')(x)
    
    # Decoder
    x = layers.Conv2D(16, (3, 3), activation='relu', padding='same')(encoded)
    x = layers.UpSampling2D((2, 2))(x)
    x = layers.Conv2D(32, (3, 3), activation='relu', padding='same')(x)
    x = layers.UpSampling2D((2, 2))(x)
    decoded = layers.Conv2D(1, (3, 3), activation='sigmoid', padding='same')(x)
    
    autoencoder = models.Model(input_img, decoded)
    autoencoder.compile(optimizer='adam', loss='mse')
    
    # 3. Train Autoencoder
    autoencoder.fit(
        x_train, x_train, # Autoencoder tries to reconstruct its input
        epochs=5,
        batch_size=32,
        shuffle=True,
        validation_data=(x_val, x_val)
    )
    
    # 4. Save Model
    os.makedirs('models', exist_ok=True)
    autoencoder.save('models/autoencoder.h5')
    print("Saved -> models/autoencoder.h5")

def build_and_train_cnn():
    print("\n--- Building and Training CNN Classifier ---")
    
    # 1. Generate faulty circuit data for CNN
    x_train, y_train = generate_synthetic_data(num_samples=800, is_faulty=True)
    x_val, y_val = generate_synthetic_data(num_samples=200, is_faulty=True)
    
    # 2. Define CNN Architecture
    cnn = models.Sequential([
        layers.Input(shape=(128, 128, 1)),
        layers.Conv2D(32, (3, 3), activation='relu'),
        layers.MaxPooling2D((2, 2)),
        layers.Conv2D(64, (3, 3), activation='relu'),
        layers.MaxPooling2D((2, 2)),
        layers.Conv2D(64, (3, 3), activation='relu'),
        layers.Flatten(),
        layers.Dense(64, activation='relu'),
        layers.Dense(4, activation='softmax') # 4 Types of Faults
    ])
    
    cnn.compile(optimizer='adam',
                loss='sparse_categorical_crossentropy',
                metrics=['accuracy'])
    
    # 3. Train CNN
    cnn.fit(
        x_train, y_train,
        epochs=5,
        batch_size=32,
        validation_data=(x_val, y_val)
    )
    
    # 4. Save Model
    cnn.save('models/cnn_classifier.h5')
    print("Saved -> models/cnn_classifier.h5")

if __name__ == '__main__':
    print("Starting Synthetic AI Model Training for VLSI Fault Detection...")
    
    # Disable GPU warnings if running on CPU
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
    
    build_and_train_autoencoder()
    build_and_train_cnn()
    
    print("\nTraining Complete! You can now test your backend API.")
