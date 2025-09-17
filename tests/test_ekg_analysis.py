import pytest
import numpy as np
from app import create_app
import json
import base64

@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    return app

@pytest.fixture
def client(app):
    return app.test_client()

def test_health_endpoint(client):
    """Test health endpoint"""
    response = client.get('/api/health')
    assert response.status_code == 200
    assert response.get_json()['status'] == 'ok'

def test_fft_analysis(client):
    """Test FFT analysis endpoint"""
    # Kreiranje test signala (sinusoida)
    fs = 250
    t = np.linspace(0, 2, fs * 2)
    test_signal = np.sin(2 * np.pi * 10 * t).tolist()  # 10 Hz sinusoida
    
    payload = {
        "signal": test_signal,
        "fs": fs
    }
    
    response = client.post('/api/analyze/fft', 
                          data=json.dumps(payload),
                          content_type='application/json')
    
    assert response.status_code == 200
    data = response.get_json()
    assert 'peak_frequency_hz' in data
    assert abs(data['peak_frequency_hz'] - 10.0) < 1.0  # Očekujemo ~10 Hz

def test_ztransform_analysis(client):
    """Test Z-transform analysis"""
    # Test signal
    test_signal = [1, 0.5, 0.25, 0.125, 0.0625] * 10  # Eksponencijalno opadajući
    
    payload = {
        "signal": test_signal,
        "fs": 250
    }
    
    response = client.post('/api/analyze/ztransform',
                          data=json.dumps(payload),
                          content_type='application/json')
    
    assert response.status_code == 200
    data = response.get_json()
    assert 'poles' in data
    assert 'zeros' in data
    assert 'stability' in data

def test_arrhythmia_detection(client):
    """Test arrhythmia detection"""
    # Simulacija EKG signala sa regularnim R-pikovima
    fs = 250
    duration = 10  # 10 sekundi
    t = np.linspace(0, duration, fs * duration)
    
    # Kreiranje osnovnog EKG signala
    heart_rate = 75  # bpm
    rr_interval = 60 / heart_rate  # sekunde
    
    ekg_signal = []
    for i in range(len(t)):
        # R-pikovi na regularnim intervalima
        if t[i] % rr_interval < 0.1:  # R-pik traje ~0.1s
            ekg_signal.append(1.0)
        else:
            ekg_signal.append(0.1 + 0.1 * np.sin(2 * np.pi * 0.5 * t[i]))
    
    payload = {
        "signal": ekg_signal,
        "fs": fs
    }
    
    response = client.post('/api/analyze/arrhythmia',
                          data=json.dumps(payload),
                          content_type='application/json')
    
    assert response.status_code == 200
    data = response.get_json()
    assert 'heart_rate' in data
    assert 'arrhythmias' in data
    assert 'r_peaks' in data

def test_complete_analysis_with_signal(client):
    """Test complete analysis with direct signal input"""
    # Test signal
    fs = 250
    t = np.linspace(0, 5, fs * 5)
    test_signal = (np.sin(2 * np.pi * 1.2 * t) + 
                   0.5 * np.sin(2 * np.pi * 2.5 * t)).tolist()
    
    payload = {
        "signal": test_signal,
        "fs": fs
    }
    
    response = client.post('/api/analyze/complete',
                          data=json.dumps(payload),
                          content_type='application/json')
    
    assert response.status_code == 200
    data = response.get_json()
    assert 'fft_analysis' in data
    assert 'z_transform' in data
    assert 'arrhythmia_detection' in data
    assert 'signal_info' in data

def test_filter_design(client):
    """Test digital filter design"""
    payload = {
        "cutoff_frequency": 40,
        "fs": 250,
        "type": "lowpass"
    }
    
    response = client.post('/api/filter/design',
                          data=json.dumps(payload),
                          content_type='application/json')
    
    assert response.status_code == 200
    data = response.get_json()
    assert 'numerator' in data
    assert 'denominator' in data
    assert 'frequency_response' in data

def test_api_info(client):
    """Test API info endpoint"""
    response = client.get('/api/info')
    assert response.status_code == 200
    data = response.get_json()
    assert 'endpoints' in data
    assert 'version' in data

def test_empty_signal_error(client):
    """Test error handling for empty signal"""
    payload = {"signal": [], "fs": 250}
    
    response = client.post('/api/analyze/fft',
                          data=json.dumps(payload),
                          content_type='application/json')
    
    assert response.status_code == 200
    data = response.get_json()
    assert 'error' in data

def test_missing_parameters(client):
    """Test error handling for missing parameters"""
    # Test bez signala
    response = client.post('/api/analyze/complete',
                          data=json.dumps({}),
                          content_type='application/json')
    
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data