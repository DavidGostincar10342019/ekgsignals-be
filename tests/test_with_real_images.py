"""
Unit testovi sa stvarnim test slikama (ekg_test1-4)
Ovaj fajl učitava stvarne slike i testira sistem
"""

import pytest
import numpy as np
import os
import base64
import sys

# Dodaj app modul u path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

class TestRealEKGImages:
    """Testovi sa stvarnim EKG slikama"""
    
    @pytest.fixture(autouse=True)
    def setup_real_images(self):
        """Učitaj stvarne test slike"""
        self.test_images_dir = os.path.join(os.path.dirname(__file__), '..', 'test_images')
        self.real_images = {}
        
        # Pokušaj da učita stvarne slike
        for i in range(1, 5):
            image_name = f'ekg_test{i}'
            image_paths = [
                os.path.join(self.test_images_dir, f'{image_name}.jpg'),
                os.path.join(self.test_images_dir, f'{image_name}.png'),
                os.path.join(self.test_images_dir, f'{image_name}.jpeg'),
                os.path.join('.', f'{image_name}.jpg'),
                os.path.join('.', f'{image_name}.png'),
                os.path.join('.', f'{image_name}.jpeg'),
            ]
            
            for image_path in image_paths:
                if os.path.exists(image_path):
                    with open(image_path, 'rb') as f:
                        image_data = f.read()
                        image_base64 = base64.b64encode(image_data).decode('utf-8')
                        self.real_images[image_name] = f"data:image/jpeg;base64,{image_base64}"
                    break
        
        print(f"Učitano {len(self.real_images)} stvarnih slika: {list(self.real_images.keys())}")
        
        if len(self.real_images) == 0:
            pytest.skip("Nema dostupnih test slika. Postavite ekg_test1.jpg, ekg_test2.jpg, ekg_test3.jpg, ekg_test4.jpg u test direktorij.")
    
    def test_real_image_processing(self):
        """Test obrade stvarnih slika"""
        from app.analysis.image_processing import process_ekg_image
        
        results = {}
        
        for image_name, image_data in self.real_images.items():
            print(f"\n🔍 Processing real image: {image_name}")
            
            result = process_ekg_image(image_data, fs=250)
            
            if 'error' not in result:
                assert 'signal' in result, f"No signal extracted from {image_name}"
                signal = result['signal']
                assert len(signal) > 100, f"Signal too short from {image_name}"
                assert not np.any(np.isnan(signal)), f"NaN values in {image_name}"
                
                results[image_name] = {
                    'signal_length': len(signal),
                    'signal_std': np.std(signal),
                    'signal_range': np.max(signal) - np.min(signal),
                    'success': True
                }
                print(f"✅ {image_name}: {len(signal)} samples, std={np.std(signal):.4f}")
            else:
                results[image_name] = {'success': False, 'error': result['error']}
                print(f"❌ {image_name}: {result['error']}")
        
        # Test da je bar polovina slika uspešno obrađena
        success_rate = sum(1 for r in results.values() if r.get('success', False)) / len(results)
        assert success_rate >= 0.5, f"Success rate too low: {success_rate:.1%}"
        
        return results
    
    def test_real_image_correlation_analysis(self):
        """Test korelacijske analize sa stvarnim slikama"""
        if len(self.real_images) < 2:
            pytest.skip("Potrebno je najmanje 2 slike za correlation analizu")
        
        from app.analysis.correlation_visualization import create_correlation_analysis_plot
        from app.analysis.image_processing import process_ekg_image
        from app.analysis.signal_to_image import compare_signals, create_normal_ekg_signal
        
        for image_name, image_data in list(self.real_images.items())[:2]:  # Test prva 2
            print(f"\n📊 Correlation analysis: {image_name}")
            
            # Izvuci signal iz slike
            result = process_ekg_image(image_data, fs=250)
            if 'error' in result:
                continue
                
            extracted_signal = result['signal']
            
            # Kreiraj referentni signal za poređenje
            reference_signal, fs = create_normal_ekg_signal(duration=len(extracted_signal)/250)
            
            # Poredi signale
            comparison = compare_signals(reference_signal, extracted_signal, fs)
            
            print(f"✅ {image_name}: Correlation={comparison['correlation']:.3f}")
            
            # Kreiraj vizualizaciju
            plot_result = create_correlation_analysis_plot(
                reference_signal, extracted_signal, fs, comparison
            )
            
            assert 'image_base64' in plot_result, f"No visualization for {image_name}"
            print(f"✅ {image_name}: Visualization created")
    
    def test_real_image_complete_pipeline(self):
        """Test kompletnog pipeline-a sa stvarnim slikama"""
        from app.analysis.image_processing import process_ekg_image
        from app.analysis.advanced_ekg_analysis import comprehensive_ekg_analysis
        from app.analysis.fft import analyze_fft
        
        pipeline_results = {}
        
        for image_name, image_data in self.real_images.items():
            print(f"\n🔄 Complete pipeline: {image_name}")
            
            try:
                # Korak 1: Image → Signal
                image_result = process_ekg_image(image_data, fs=250)
                if 'error' in image_result:
                    print(f"⚠️ {image_name}: Image processing failed - {image_result['error']}")
                    continue
                
                signal = image_result['signal']
                
                # Korak 2: EKG Analysis
                ekg_result = comprehensive_ekg_analysis(signal, 250)
                
                # Korak 3: FFT Analysis
                fft_result = analyze_fft(signal, 250)
                
                pipeline_results[image_name] = {
                    'image_processing': 'success',
                    'ekg_analysis': len(ekg_result) > 0,
                    'fft_analysis': 'peak_frequency_hz' in fft_result,
                    'signal_length': len(signal)
                }
                
                print(f"✅ {image_name}: Pipeline completed")
                
            except Exception as e:
                pipeline_results[image_name] = {'error': str(e)}
                print(f"❌ {image_name}: Pipeline failed - {e}")
        
        # Test da je bar jedan pipeline prošao
        successful_pipelines = sum(1 for r in pipeline_results.values() 
                                 if r.get('image_processing') == 'success')
        assert successful_pipelines > 0, "No successful pipelines with real images"
        
        print(f"\n📈 Successfully processed {successful_pipelines}/{len(self.real_images)} real images")
        
        return pipeline_results

def test_real_images_integration():
    """Glavna funkcija za testiranje sa stvarnim slikama"""
    test_instance = TestRealEKGImages()
    test_instance.setup_real_images()
    
    if len(test_instance.real_images) == 0:
        print("⚠️ Nema dostupnih test slika za testiranje")
        return False
    
    try:
        # Test image processing
        processing_results = test_instance.test_real_image_processing()
        
        # Test correlation analysis
        test_instance.test_real_image_correlation_analysis()
        
        # Test complete pipeline
        pipeline_results = test_instance.test_real_image_complete_pipeline()
        
        print("\n🎉 SVI TESTOVI SA STVARNIM SLIKAMA PROŠLI!")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST SA STVARNIM SLIKAMA NEUSPEŠAN: {e}")
        return False

if __name__ == "__main__":
    success = test_real_images_integration()
    sys.exit(0 if success else 1)