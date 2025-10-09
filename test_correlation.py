
import requests
import base64
import json

def test_image_correlation(image_path):
    """
    Tests the correlation of an EKG image by sending it to the Flask API.
    """
    try:
        # Read and encode the image
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')

        # Prepare the payload
        payload = {
            "image": f"data:image/png;base64,{encoded_string}",
            "fs": 250  # Default sampling frequency
        }

        # Send the request
        url = "http://127.0.0.1:8000/test/signal-image-roundtrip"
        response = requests.post(url, json=payload)
        response.raise_for_status()  # Raise an exception for bad status codes

        # Process the response
        result = response.json()
        
        if result.get('success'):
            correlation = result.get('round_trip_results', {}).get('comparison', {}).get('correlation')
            if correlation is not None:
                print(f"Correlation for {image_path}: {correlation:.4f}")
            else:
                print(f"Error: Could not find correlation in response for {image_path}.")
                print("Full response:", json.dumps(result, indent=2))
        else:
            print(f"API returned an error for {image_path}:")
            print(json.dumps(result, indent=2))

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
    except FileNotFoundError:
        print(f"Error: Image file not found at {image_path}")

if __name__ == "__main__":
    test_image_correlation("app/static/images/testslika1.png")
