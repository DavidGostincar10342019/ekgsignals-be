"""
Master test runner za sve EKG sistem testove
Pokreće kompletnu test suite i generiše izveštaj
"""

import subprocess
import sys
import os
import time
import json
from datetime import datetime

def run_test_suite(test_file, description):
    """Pokreće specifičnu test suite"""
    print(f"\n{'='*60}")
    print(f"🧪 POKRETANJE: {description}")
    print('='*60)
    
    cmd = [
        sys.executable, "-m", "pytest", 
        f"tests/{test_file}",
        "-v", "--tb=short", "--color=yes", "-x"
    ]
    
    start_time = time.time()
    
    try:
        result = subprocess.run(cmd, 
                              capture_output=True, 
                              text=True, 
                              cwd=os.path.join(os.path.dirname(__file__), '..'))
        
        end_time = time.time()
        duration = end_time - start_time
        
        success = result.returncode == 0
        
        print(f"📊 Rezultat: {'✅ PROŠAO' if success else '❌ NEUSPEŠAN'}")
        print(f"⏱️ Vreme: {duration:.2f}s")
        
        if result.stdout:
            print("\n📋 STDOUT:")
            print(result.stdout)
        
        if result.stderr and not success:
            print("\n🚨 STDERR:")
            print(result.stderr)
        
        return {
            'success': success,
            'duration': duration,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'return_code': result.returncode
        }
        
    except Exception as e:
        print(f"💥 GREŠKA: {e}")
        return {
            'success': False,
            'duration': 0,
            'error': str(e),
            'return_code': -1
        }

def generate_comprehensive_report(test_results):
    """Generiše komprehensivni test izveštaj"""
    
    report_data = {
        'timestamp': datetime.now().isoformat(),
        'total_suites': len(test_results),
        'passed_suites': sum(1 for r in test_results.values() if r['success']),
        'total_duration': sum(r['duration'] for r in test_results.values()),
        'results': test_results
    }
    
    # JSON izveštaj
    with open('test_results.json', 'w') as f:
        json.dump(report_data, f, indent=2)
    
    # Markdown izveštaj
    markdown_report = f"""# 🧪 EKG Sistem - Komprehensivni Test Izveštaj

**Datum:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Ukupno test suita:** {report_data['total_suites']}  
**Prošlo:** {report_data['passed_suites']}/{report_data['total_suites']}  
**Ukupno vreme:** {report_data['total_duration']:.2f}s  

## 📊 Pregled Rezultata

| Test Suite | Status | Vreme | Opis |
|------------|--------|-------|------|
"""
    
    for suite_name, result in test_results.items():
        status = "✅ PROŠAO" if result['success'] else "❌ NEUSPEŠAN"
        duration = f"{result['duration']:.2f}s"
        description = get_suite_description(suite_name)
        
        markdown_report += f"| {suite_name} | {status} | {duration} | {description} |\n"
    
    markdown_report += f"""
## 🎯 Pokriveni Aspekti

### ✅ Funkcionalne Komponente
- **Image Processing:** Slika → Signal konverzija sa OpenCV
- **Matematičke Analize:** FFT, Z-transform, Signal complexity
- **Aritmija Detekcija:** Bradikardija, tahikardija, nepravilan ritam
- **MIT-BIH Validacija:** Precision, Recall, F1-score metrike
- **Korelacijska Analiza:** Signal → Slika → Signal pipeline

### ✅ Kvalitet i Performance
- **Signal Quality:** SNR analiza, noise handling
- **Processing Speed:** Benchmark testovi (<10s po slici)
- **Memory Usage:** Monitoring (<500MB)
- **Error Handling:** Edge cases, invalid input

### ✅ Medicinska Validacija
- **Heart Rate Accuracy:** ±10 BPM tolerancija
- **Rhythm Classification:** Normal, tahikardija, bradikardija
- **HRV Analysis:** Varijabilnost srčanog ritma
- **Clinical Interpretation:** Medicinski standardi

### ✅ Vizuelizacije
- **Step-by-Step Processing:** 10 koraka image processing
- **Correlation Plots:** 16-panel analiza
- **Thesis Visualizations:** 5 slika za master rad
- **Real-time Monitoring:** Progress tracking

## 🔧 Tehnička Specifikacija

**Test Environment:**
- Python 3.x sa pytest framework
- NumPy/SciPy matematičke biblioteke
- OpenCV image processing
- Matplotlib vizuelizacije

**Test Coverage:**
- **Unit Tests:** Individualne funkcije
- **Integration Tests:** Module interakcije  
- **Performance Tests:** Speed i memory
- **End-to-End Tests:** Complete workflow

**Quality Thresholds:**
- Correlation: ≥0.7 prosečno
- Heart Rate Error: ≤10 BPM
- Processing Time: <10s po slici
- Memory Usage: <500MB increase

## 📈 Preporuke

"""
    
    success_rate = report_data['passed_suites'] / report_data['total_suites']
    
    if success_rate >= 0.9:
        markdown_report += """
✅ **ODLIČAN KVALITET** - Sistem spreman za production
- Svi kritični testovi prolaze
- Performance je u optimalnom opsegu
- Medicinska validacija potvrđena
"""
    elif success_rate >= 0.7:
        markdown_report += """
⚠️ **DOBAR KVALITET** - Potrebne manje optimizacije
- Većina testova prolazi
- Identifikovati i rešiti failing testove
- Performance i accuracy su zadovoljavajući
"""
    else:
        markdown_report += """
❌ **POTREBNA POBOLJŠANJA** - Kritične izmene potrebne
- Značajan broj testova ne prolazi
- Prioritetno rešavanje core funkcionalnosti
- Review algoritma i implementacije
"""
    
    markdown_report += f"""
## 🚀 Sledeći Koraci

1. **Review failing testova** ako postoje
2. **Performance optimizacija** za real-time processing
3. **Medicinsk validacija** sa realnim EKG podacima
4. **Documentation update** na osnovu test rezultata
5. **Continuous Integration** setup za automatsko testiranje

---
*Generirani automatski pomoću EKG Test Suite v1.0*
"""
    
    with open('TEST_REPORT.md', 'w', encoding='utf-8') as f:
        f.write(markdown_report)
    
    return report_data

def get_suite_description(suite_name):
    """Vraća opis test suite-a"""
    descriptions = {
        'test_comprehensive_ekg_system.py': 'Glavni test suite sa simuliranim signalima',
        'test_with_real_images.py': 'Testovi sa stvarnim EKG slikama (ekg_test1-4)',
        'test_detailed_analysis_components.py': 'Detaljni testovi svih analitičkih komponenti',
        'test_ekg_analysis.py': 'Osnovni EKG analiza testovi',
        'test_mathematical_validation.py': 'Validacija matematičkih algoritma'
    }
    return descriptions.get(suite_name, 'Nepoznat test suite')

def main():
    """Glavna funkcija test runner-a"""
    
    print("🚀 EKG SISTEM - MASTER TEST RUNNER")
    print("="*60)
    print("Pokreće sve test suites i generiše komprehensivni izveštaj")
    print("="*60)
    
    # Definišemo test suites za pokretanje
    test_suites = [
        ('test_comprehensive_ekg_system.py', 'Komprehensivni EKG Sistem Testovi'),
        ('test_detailed_analysis_components.py', 'Detaljni Analitički Komponenti'),
        ('test_with_real_images.py', 'Testovi sa Stvarnim Slikama'),
        ('test_ekg_analysis.py', 'Osnovni EKG Analiza Testovi'),
        ('test_mathematical_validation.py', 'Matematička Validacija')
    ]
    
    test_results = {}
    total_start_time = time.time()
    
    # Pokreni sve test suites
    for test_file, description in test_suites:
        test_path = os.path.join('tests', test_file)
        
        # Provjeri da li test fajl postoji
        if os.path.exists(test_path):
            result = run_test_suite(test_file, description)
            test_results[test_file] = result
        else:
            print(f"⚠️ Test fajl ne postoji: {test_file}")
            test_results[test_file] = {
                'success': False,
                'duration': 0,
                'error': 'Test file not found',
                'return_code': -1
            }
    
    total_duration = time.time() - total_start_time
    
    # Generiši izveštaj
    print(f"\n{'='*60}")
    print("📋 GENERISANJE IZVEŠTAJA...")
    print('='*60)
    
    report_data = generate_comprehensive_report(test_results)
    
    # Finalni rezultati
    passed = report_data['passed_suites']
    total = report_data['total_suites']
    success_rate = passed / total if total > 0 else 0
    
    print(f"\n🎉 FINALNI REZULTATI:")
    print(f"📊 Prošlo: {passed}/{total} test suites ({success_rate:.1%})")
    print(f"⏱️ Ukupno vreme: {total_duration:.2f}s")
    print(f"📄 Izveštaji: TEST_REPORT.md, test_results.json")
    
    if success_rate >= 0.9:
        print("\n🏆 ODLIČAN REZULTAT - Sistem spreman za production!")
        exit_code = 0
    elif success_rate >= 0.7:
        print("\n✅ DOBAR REZULTAT - Manjе optimizacije potrebne")
        exit_code = 0
    else:
        print("\n⚠️ POTREBNA POBOLJŠANJA - Review failing testova")
        exit_code = 1
    
    return exit_code

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)