import cv2
import numpy as np
import pytest
import os
import matplotlib.pyplot as plt
from app.analysis.image_processing_visualization import process_image_step_by_step

# Definišemo putanju do test slike i izlaznog direktorijuma
# Koristimo relativne putanje od roota projekta
TEST_IMAGE_PATH = os.path.join(os.path.dirname(__file__), '../app/static/images/test slika.png')
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '../generated_plots')

@pytest.mark.parametrize("image_filename", ["testslika1.png", "testslika2.png", "testslika3.png", "testslika4.png", "testslika5.png"])
def test_image_processing_pipeline(image_filename):
    """ 
    Testira kompletan pipeline za obradu slike i čuva međurezultate.
    """
    # Definišemo putanje
    test_image_path = os.path.join(os.path.dirname(__file__), '../app/static/images', image_filename)
    output_dir = os.path.join(os.path.dirname(__file__), '../generated_plots')

    # Učitavanje slike
    if not os.path.exists(test_image_path):
        pytest.fail(f"Test slika nije pronađena na putanji: {test_image_path}")
    test_image = cv2.imread(test_image_path)
    assert test_image is not None, f"Slika {image_filename} se nije mogla učitati"

    # Kreiraj izlazni direktorijum ako ne postoji
    os.makedirs(output_dir, exist_ok=True)

    # 1. Pokreni obradu slike
    processing_steps = process_image_step_by_step(test_image)

    # 2. Proveri da li je proces uspeo i vratio signal
    assert "error" not in processing_steps, f"Došlo je do greške u pipeline-u za sliku {image_filename}: {processing_steps.get('error')}"
    assert "final_signal" in processing_steps, f"Finalni signal nedostaje u rezultatima za {image_filename}"
    final_signal = processing_steps["final_signal"]
    assert isinstance(final_signal, list), f"Finalni signal za {image_filename} nije lista"
    assert len(final_signal) > 0, f"Finalni signal za {image_filename} je prazan"

    # 3. Sačuvaj ključne međukorake kao slike za vizuelnu inspekciju
    image_prefix = os.path.splitext(image_filename)[0].replace(" ", "_")
    steps_to_save = {
        f"{image_prefix}_step_4_binary.png": processing_steps.get("step_4_binary"),
        f"{image_prefix}_step_5_grid_detected.png": processing_steps.get("step_5_grid_detected"),
        f"{image_prefix}_step_6_grid_removed.png": processing_steps.get("step_6_grid_removed"),
        f"{image_prefix}_step_7_cleaned.png": processing_steps.get("step_7_cleaned"),
    }

    for filename, image_data in steps_to_save.items():
        assert image_data is not None, f"Međukorak {filename} za {image_filename} nije generisan."
        output_path = os.path.join(output_dir, f"unittest_{filename}")
        cv2.imwrite(output_path, image_data)
        print(f"Sačuvan međukorak: {output_path}")

    # 4. Sačuvaj finalni signal kao plot
    plt.figure(figsize=(10, 4))
    plt.plot(final_signal)
    plt.title(f"Final Extracted Signal for {image_filename}")
    plt.grid(True)
    plot_path = os.path.join(output_dir, f"unittest_{image_prefix}_final_signal.png")
    plt.savefig(plot_path)
    plt.close()
    print(f"Sačuvan grafik signala: {plot_path}")
