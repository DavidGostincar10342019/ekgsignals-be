import pytest
import numpy as np
from scipy.stats import pearsonr
from scipy import signal as scipy_signal
import os
import cv2
import base64

# Importujemo ključne funkcije iz projekta
from app.analysis.signal_to_image import create_ekg_image_from_signal
from app.analysis.image_processing_visualization import process_image_step_by_step

# Prag korelacije koji želimo da postignemo
CORRELATION_THRESHOLD = 0.8

@pytest.mark.parametrize("image_filename", [
    "testslika1.png", 
    "testslika2.png", 
    "testslika3.png", 
    "testslika4.png", 
    "testslika5.png"
])
def test_round_trip_correlation_on_real_images(image_filename):
    """
    Testira round-trip korelacionu konzistentnost na stvarnim slikama.
    (Slika -> Signal A -> Slika -> Signal B), poredi A i B.
    """
    # 1. Učitaj originalnu sliku
    image_path = os.path.join(os.path.dirname(__file__), '../app/static/images', image_filename)
    if not os.path.exists(image_path):
        pytest.fail(f"Test slika nije pronađena: {image_path}")
    original_image = cv2.imread(image_path)
    assert original_image is not None, f"Slika {image_filename} se nije mogla učitati."

    # 2. Korak 1: Originalna Slika -> Signal A
    processing_results_A = process_image_step_by_step(original_image)
    assert "error" not in processing_results_A, f"[A] Obrada slike {image_filename} nije uspela: {processing_results_A.get('error')}"
    signal_A = np.array(processing_results_A.get("final_signal", []))
    assert len(signal_A) > 0, f"[A] Ekstraktovani signal za {image_filename} je prazan."

    # 3. Korak 2: Signal A -> Rekonstruisana Slika
    fs = 250 # Pretpostavljena frekvencija
    reconstructed_image_data = create_ekg_image_from_signal(signal_A.tolist(), fs=fs, style="clinical")
    img_b64 = reconstructed_image_data['image_base64']
    img_data = base64.b64decode(img_b64.split(',')[1])
    nparr = np.frombuffer(img_data, np.uint8)
    reconstructed_image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    assert reconstructed_image is not None, f"[B] Kreiranje slike iz Signala A za {image_filename} nije uspelo."

    # 4. Korak 3: Rekonstruisana Slika -> Signal B
    processing_results_B = process_image_step_by_step(reconstructed_image)
    assert "error" not in processing_results_B, f"[B] Obrada rekonstruisane slike za {image_filename} nije uspela: {processing_results_B.get('error')}"
    signal_B = np.array(processing_results_B.get("final_signal", []))
    assert len(signal_B) > 0, f"[B] Ekstraktovani signal za {image_filename} je prazan."

    # 5. Poređenje: Signal A vs Signal B
    len_A, len_B = len(signal_A), len(signal_B)
    if len_A != len_B:
        signal_B = scipy_signal.resample(signal_B, len_A)

    correlation, p_value = pearsonr(signal_A, signal_B)
    
    print(f"\n--- Round-Trip Correlation for {image_filename} ---")
    print(f"Pearson r: {correlation:.4f}")
    print(f"--------------------------------------------------")

    assert correlation > CORRELATION_THRESHOLD, f"Korelacija {correlation:.4f} za sliku {image_filename} je ispod praga od {CORRELATION_THRESHOLD}"
