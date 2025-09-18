#!/usr/bin/env python3
"""
Kompletni test suite za validaciju matematičkih formula u EKG projektu

Testira:
1. FFT analizu i harmonijske komponente
2. THD računanje
3. Z-transformaciju i AR koeficijente
4. SFI formulu (pre i posle ispravke)
5. Numeričku stabilnost
6. Edge cases i granične slučajeve
"""

import unittest
import numpy as np
import sys
import os
from unittest.mock import patch

# Dodaj putanju do app modula
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from analysis.fft import analyze_fft, analyze_sine_wave_components
from analysis.ztransform import z_transform_analysis, estimate_ar_coefficients
from analysis.advanced_ekg_analysis import spatial_filling_index


class TestFFTAnalysis(unittest.TestCase):
    """Test FFT analize i harmonijskih komponenti"""
    
    def setUp(self):
        """Priprema test signala"""
        self.fs = 1000
        self.t = np.linspace(0, 2, self.fs * 2)
        
    def test_pure_sine_wave(self):
        """Test čistog sinusnog signala"""
        freq = 5.0  # Hz
        amplitude = 2.0
        signal = amplitude * np.sin(2 * np.pi * freq * self.t)
        
        result = analyze_fft(signal, self.fs)
        
        # Provera osnovnih parametara
        self.assertAlmostEqual(result['peak_frequency_hz'], freq, places=1)
        self.assertGreater(result['peak_amplitude'], amplitude * 0.8)  # Tolerancija zbog diskretizacije
        self.assertTrue(result['dc_removed'])
        
        # Provera sine wave analize
        sine_analysis = result['sine_wave_analysis']
        self.assertGreater(sine_analysis['spectral_purity_percent'], 80)
        self.assertLess(sine_analysis['thd_percent'], 5)
        self.assertEqual(sine_analysis['sine_wave_confidence'], 'visoka')
        
    def test_harmonic_signal_thd(self):
        """Test THD računanja sa poznatim harmonicima"""
        fundamental_freq = 10.0
        fund_amp = 1.0
        h2_amp = 0.3  # 30%
        h3_amp = 0.1  # 10%
        
        signal = (fund_amp * np.sin(2*np.pi*fundamental_freq*self.t) + 
                 h2_amp * np.sin(2*np.pi*2*fundamental_freq*self.t) + 
                 h3_amp * np.sin(2*np.pi*3*fundamental_freq*self.t))
        
        result = analyze_fft(signal, self.fs)
        sine_analysis = result['sine_wave_analysis']
        
        # Teorijski THD = sqrt(0.3² + 0.1²) / 1.0 * 100 = 31.62%
        theoretical_thd = (np.sqrt(h2_amp**2 + h3_amp**2) / fund_amp) * 100
        measured_thd = sine_analysis['thd_percent']
        
        self.assertAlmostEqual(measured_thd, theoretical_thd, delta=5.0)
        self.assertGreaterEqual(len(sine_analysis['detected_harmonics']), 2)
        
    def test_dc_component_removal(self):
        """Test uklanjanja DC komponente"""
        dc_offset = 5.0
        signal = dc_offset + np.sin(2 * np.pi * 1 * self.t)
        
        result = analyze_fft(signal, self.fs)
        
        # DC komponenta treba da bude detektovana ali uklonjena iz analize
        self.assertGreater(result['dc_component'], dc_offset * 0.8)
        self.assertTrue(result['dc_removed'])
        
    def test_noise_signal(self):
        """Test signala sa šumom"""
        np.random.seed(42)
        noise_signal = np.random.normal(0, 1, len(self.t))
        
        result = analyze_fft(noise_signal, self.fs)
        sine_analysis = result['sine_wave_analysis']
        
        # Šum treba da ima nisku spectral purity i visoku kompleksnost
        self.assertLess(sine_analysis['spectral_purity_percent'], 40)
        self.assertEqual(sine_analysis['sine_wave_confidence'], 'vrlo niska')


class TestZTransformAnalysis(unittest.TestCase):
    """Test Z-transformacije i AR modeliranja"""
    
    def test_known_ar_process(self):
        """Test sa poznatim AR(2) procesom"""
        # AR(2): x[n] = 0.5*x[n-1] - 0.2*x[n-2] + w[n]
        true_coeffs = [0.5, -0.2]
        
        np.random.seed(42)
        n_samples = 1000
        noise = np.random.normal(0, 0.1, n_samples)
        
        signal_ar = np.zeros(n_samples)
        for i in range(2, n_samples):
            signal_ar[i] = (true_coeffs[0] * signal_ar[i-1] + 
                           true_coeffs[1] * signal_ar[i-2] + 
                           noise[i])
        
        # Test AR procenitelja
        estimated_coeffs = estimate_ar_coefficients(signal_ar, order=2)
        
        # Provera tačnosti procene
        for i, (true_val, est_val) in enumerate(zip(true_coeffs, estimated_coeffs[:2])):
            self.assertAlmostEqual(est_val, true_val, delta=0.15,
                                 msg=f"AR koeficijent {i+1}: {est_val} != {true_val}")
    
    def test_stability_analysis(self):
        """Test analize stabilnosti sistema"""
        # Kreiranje stabilnog signala
        stable_signal = np.sin(2*np.pi*1*np.linspace(0, 2, 500))
        
        result = z_transform_analysis(stable_signal, fs=250)
        
        if 'stability' in result:
            stability = result['stability']
            self.assertTrue(stability['stable'])
            self.assertLess(stability['max_pole_magnitude'], 1.0)
            self.assertGreater(stability['poles_inside_unit_circle'], 0)
            
    def test_empty_signal(self):
        """Test sa praznim signalom"""
        empty_signal = []
        result = z_transform_analysis(empty_signal)
        
        self.assertIn('error', result)
        
    def test_constant_signal_robustness(self):
        """Test numeričke stabilnosti sa konstantnim signalom"""
        constant_signal = np.ones(100) * 5.0
        
        # Ovaj test treba da provjeri da li je dodana zaštita
        result = z_transform_analysis(constant_signal)
        
        # Ne smije da krahira - mora imati ili rezultat ili error
        self.assertTrue('error' in result or 'stability' in result)


class TestSpatialFillingIndex(unittest.TestCase):
    """Test SFI formule - pre i posle ispravke"""
    
    def setUp(self):
        """Priprema test signala"""
        self.fs = 250
        self.t = np.linspace(0, 2, self.fs * 2)
        
    def test_sine_wave_sfi(self):
        """Test SFI za sinusni signal"""
        signal = np.sin(2 * np.pi * 1 * self.t)
        result = spatial_filling_index(signal)
        
        sfi = result['spatial_filling_index']
        
        # Za regularni sinusni signal, SFI treba da bude u razumnom opsegu
        self.assertGreater(sfi, 0.5, "SFI prezemalno za sinusni signal")
        self.assertLess(sfi, 3.0, "SFI previsoko za sinusni signal")
        
    def test_linear_signal_sfi(self):
        """Test SFI za linearni signal"""
        signal = np.linspace(-1, 1, len(self.t))
        result = spatial_filling_index(signal)
        
        sfi = result['spatial_filling_index']
        
        # Linearni signal treba da ima nisku kompleksnost
        self.assertIsInstance(sfi, (int, float))
        self.assertFalse(np.isnan(sfi))
        
    def test_noise_signal_sfi(self):
        """Test SFI za šum"""
        np.random.seed(42)
        noise_signal = np.random.normal(0, 1, len(self.t))
        result = spatial_filling_index(noise_signal)
        
        sfi = result['spatial_filling_index']
        
        # Šum treba da ima višu kompleksnost od regularnog signala
        self.assertIsInstance(sfi, (int, float))
        self.assertFalse(np.isnan(sfi))
        
    def test_sfi_components(self):
        """Test komponenti SFI kalkulacije"""
        signal = np.sin(2 * np.pi * 2 * self.t)
        result = spatial_filling_index(signal)
        
        # Proveri da sve komponente postoje
        self.assertIn('total_path_length', result)
        self.assertIn('average_amplitude', result)
        self.assertIn('signal_points', result)
        
        # Provjeri da su pozitivne
        self.assertGreater(result['total_path_length'], 0)
        self.assertGreater(result['average_amplitude'], 0)
        self.assertEqual(result['signal_points'], len(signal))


class TestNumericalStability(unittest.TestCase):
    """Test numeričke stabilnosti algoritama"""
    
    def test_very_small_signals(self):
        """Test sa veoma malim signalima"""
        tiny_signal = np.array([1e-15, 2e-15, 1e-15]) * np.sin(np.linspace(0, 1, 3))
        
        # FFT test
        fft_result = analyze_fft(tiny_signal, 250)
        self.assertNotIn('error', fft_result)
        
        # SFI test  
        sfi_result = spatial_filling_index(tiny_signal)
        self.assertFalse(np.isnan(sfi_result['spatial_filling_index']))
        
    def test_very_large_signals(self):
        """Test sa veoma velikim signalima"""
        large_signal = np.array([1e10, 2e10, 1.5e10, 0.8e10])
        
        # FFT test
        fft_result = analyze_fft(large_signal, 250)
        self.assertNotIn('error', fft_result)
        
        # SFI test
        sfi_result = spatial_filling_index(large_signal)
        self.assertFalse(np.isnan(sfi_result['spatial_filling_index']))
        
    def test_zero_signal(self):
        """Test sa nula signalom"""
        zero_signal = np.zeros(100)
        
        # SFI treba da vrati 0 ili error
        sfi_result = spatial_filling_index(zero_signal)
        sfi = sfi_result['spatial_filling_index']
        self.assertTrue(sfi == 0 or np.isnan(sfi))
        
    def test_single_point_signal(self):
        """Test sa jednom tačkom"""
        single_point = np.array([1.0])
        
        # Ne smije da krahira
        try:
            fft_result = analyze_fft(single_point, 250)
            sfi_result = spatial_filling_index(single_point)
            # Test prošao ako nema exception
            self.assertTrue(True)
        except Exception as e:
            self.fail(f"Single point signal uzrokovao grešku: {e}")


class TestEdgeCases(unittest.TestCase):
    """Test granične slučajeve"""
    
    def test_different_sampling_rates(self):
        """Test sa različitim frekvencijama uzorkovanja"""
        signal = np.sin(2*np.pi*5*np.linspace(0, 1, 500))
        
        sampling_rates = [125, 250, 500, 1000]
        
        for fs in sampling_rates:
            with self.subTest(fs=fs):
                result = analyze_fft(signal, fs)
                self.assertNotIn('error', result)
                self.assertIsInstance(result['peak_frequency_hz'], (int, float))
                
    def test_non_power_of_two_lengths(self):
        """Test sa dužinama koje nisu stepen dvojke"""
        lengths = [100, 137, 255, 333, 777]
        
        for length in lengths:
            with self.subTest(length=length):
                signal = np.sin(2*np.pi*1*np.linspace(0, 1, length))
                result = analyze_fft(signal, 250)
                self.assertNotIn('error', result)
                
    def test_nyquist_frequency_signal(self):
        """Test sa signalom na Nyquist frekvenciji"""
        fs = 250
        nyquist_freq = fs / 2
        t = np.linspace(0, 1, fs)
        signal = np.sin(2*np.pi*nyquist_freq*t)
        
        result = analyze_fft(signal, fs)
        self.assertNotIn('error', result)


def run_comprehensive_tests():
    """Pokreni sve testove i generiši report"""
    
    # Kreiranje test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Dodavanje test slasa
    test_classes = [
        TestFFTAnalysis,
        TestZTransformAnalysis, 
        TestSpatialFillingIndex,
        TestNumericalStability,
        TestEdgeCases
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Pokretanje testova
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)
    
    # Generiši summary report
    print("\n" + "="*60)
    print("📊 MATEMATIČKA VALIDACIJA - FINALNI REPORT")
    print("="*60)
    print(f"🧪 Ukupno testova: {result.testsRun}")
    print(f"✅ Prošli: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"❌ Neuspešni: {len(result.failures)}")
    print(f"💥 Greške: {len(result.errors)}")
    
    if result.failures:
        print("\n❌ NEUSPEŠNI TESTOVI:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback.split(chr(10))[-2]}")
    
    if result.errors:
        print("\n💥 GREŠKE:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback.split(chr(10))[-2]}")
    
    success_rate = ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun) * 100
    print(f"\n🎯 USPEŠNOST: {success_rate:.1f}%")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_comprehensive_tests()
    sys.exit(0 if success else 1)