"""
Démonstration du système de raisonnement HOPPER
Planification, génération de code, exécution et apprentissage
"""

import asyncio
import sys
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.reasoning import (
    ProblemSolver,
    Problem,
    DecompositionStrategy,
    CodeExecutor,
    SecurityLevel,
    CodeGenerator,
    GenerationConfig,
    CodeQuality,
    ExperienceManager,
    LearningStrategy
)


async def demo_problem_solving():
    """Démonstration de résolution de problèmes"""
    print("\n" + "=" * 80)
    print("DÉMONSTRATION 1: RÉSOLUTION DE PROBLÈMES COMPLEXES")
    print("=" * 80 + "\n")
    
    solver = ProblemSolver()
    
    # Définir un problème complexe
    problem = Problem(
        id="prob_001",
        description="Optimiser le traitement de 1 million de lignes CSV",
        category="optimization",
        complexity=7,
        constraints={
            'max_memory': '256MB',
            'max_time': '30s',
            'parallel_ok': True
        },
        success_criteria=[
            "Temps < 30s",
            "Mémoire < 256MB",
            "Aucune donnée perdue"
        ],
        resources_needed=['pandas', 'multiprocessing', 'csv']
    )
    
    print(f"📋 Problème: {problem.description}")
    print(f"   Catégorie: {problem.category}")
    print(f"   Complexité: {problem.complexity}/10")
    print(f"   Contraintes: {len(problem.constraints)}")
    
    # Analyser le problème
    print("\n🔍 Analyse du problème...")
    analysis = await solver.analyze_problem(problem)
    print(f"   Niveau de complexité: {analysis['complexity_assessment']['level']}")
    print(f"   Stratégie recommandée: {analysis['recommended_strategy'].value}")
    print(f"   Étapes estimées: {analysis['estimated_steps']}")
    print(f"   Risques identifiés: {len(analysis['risk_factors'])}")
    
    # Décomposer
    print("\n📊 Décomposition du problème...")
    strategy = analysis['recommended_strategy']
    steps = await solver.decompose_problem(problem, strategy)
    print(f"   {len(steps)} étapes créées")
    
    for i, step in enumerate(steps[:5], 1):  # Afficher les 5 premières
        print(f"   {i}. {step.description}")
    
    if len(steps) > 5:
        print(f"   ... et {len(steps) - 5} autres étapes")
    
    # Exécuter
    print("\n⚙️  Exécution du plan...")
    solution = await solver.execute_plan(problem, steps, strategy)
    
    print(f"   ✓ Terminé en {solution.actual_time:.2f}s")
    print(f"   ✓ Confiance: {solution.confidence:.0%}")
    print(f"   ✓ Succès: {solution.success}")
    print(f"   ✓ Étapes complétées: {sum(1 for s in steps if s.status.value == 'completed')}/{len(steps)}")
    
    if solution.lessons_learned:
        print(f"\n💡 Leçons apprises:")
        for lesson in solution.lessons_learned:
            print(f"   - {lesson}")


async def demo_code_execution():
    """Démonstration d'exécution de code sécurisée"""
    print("\n" + "=" * 80)
    print("DÉMONSTRATION 2: EXÉCUTION DE CODE SÉCURISÉE")
    print("=" * 80 + "\n")
    
    executor = CodeExecutor(security_level=SecurityLevel.HIGH)
    
    print(f"🔒 Niveau de sécurité: {executor.security_level.value}")
    print(f"   Timeout: {executor.resource_limits['timeout']}s")
    print(f"   Mémoire max: {executor.resource_limits['max_memory'] / (1024*1024):.0f}MB")
    
    # Test 1: Code simple
    print("\n📝 Test 1: Calcul mathématique")
    code1 = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

result = fibonacci(10)
print(f"Fibonacci(10) = {result}")
"""
    
    result1 = await executor.execute_python(code1)
    print(f"   ✓ Succès: {result1.success}")
    print(f"   ✓ Temps: {result1.execution_time:.3f}s")
    print(f"   ✓ Sortie: {result1.output.strip()}")
    
    # Test 2: Code avec boucles
    print("\n📝 Test 2: Traitement de données")
    code2 = """
data = list(range(1000))
result = sum(x ** 2 for x in data if x % 2 == 0)
print(f"Somme des carrés des pairs: {result}")
"""
    
    result2 = await executor.execute_python(code2)
    print(f"   ✓ Succès: {result2.success}")
    print(f"   ✓ Temps: {result2.execution_time:.3f}s")
    print(f"   ✓ Sortie: {result2.output.strip()}")
    
    # Test 3: Code dangereux (sera bloqué)
    print("\n📝 Test 3: Code potentiellement dangereux")
    code3 = """
import os
os.system('rm -rf /')
"""
    
    result3 = await executor.execute_python(code3)
    print(f"   ✓ Bloqué: {not result3.success}")
    print(f"   ✓ Raison: {result3.error}")
    
    # Test 4: Tests automatiques
    print("\n📝 Test 4: Tests automatiques d'une fonction")
    test_code = """
def add(a, b):
    return a + b
"""
    
    test_cases = [
        {'input': '1, 2', 'expected': 3},
        {'input': '0, 0', 'expected': 0},
        {'input': '-1, 1', 'expected': 0}
    ]
    
    # Note: test_code nécessite une fonction test() pour fonctionner
    print(f"   Tests préparés: {len(test_cases)} cas")
    
    # Statistiques
    print("\n📊 Statistiques d'exécution:")
    stats = executor.get_stats()
    print(f"   Exécutions totales: {stats['total_executions']}")
    print(f"   Taux de succès: {stats['success_rate']:.0%}")
    print(f"   Temps moyen: {stats['average_time']:.3f}s")


async def demo_code_generation():
    """Démonstration de génération de code"""
    print("\n" + "=" * 80)
    print("DÉMONSTRATION 3: GÉNÉRATION DE CODE INTELLIGENTE")
    print("=" * 80 + "\n")
    
    config = GenerationConfig(
        quality=CodeQuality.PRODUCTION,
        add_docstrings=True,
        add_type_hints=True,
        add_error_handling=True,
        add_tests=True
    )
    
    generator = CodeGenerator(config)
    
    # Générer une fonction
    print("📝 Génération d'une fonction de traitement de données")
    
    function_code = await generator.generate_function(
        name="process_user_data",
        purpose="Filtrer et transformer les données utilisateurs",
        inputs=[
            {'name': 'users', 'type': 'List[Dict]', 'description': 'Liste des utilisateurs'},
            {'name': 'min_age', 'type': 'int', 'description': 'Âge minimum'}
        ],
        output_type="List[Dict]",
        logic="""filtered = [u for u in users if u.get('age', 0) >= min_age]
    return [{'name': u['name'], 'age': u['age']} for u in filtered]"""
    )
    
    print("\n" + "─" * 80)
    print(function_code)
    print("─" * 80)
    
    # Générer une classe
    print("\n\n📦 Génération d'une classe")
    
    class_code = await generator.generate_class(
        name="DataProcessor",
        purpose="Processeur de données avec cache",
        attributes=[
            {'name': 'cache_size', 'type': 'int', 'default': '100'},
            {'name': 'cache', 'type': 'Dict', 'default': '{}'}
        ],
        methods=[
            {
                'name': 'process',
                'params': [{'name': 'data', 'type': 'Any'}],
                'purpose': 'Traite les données',
                'body': 'return data'
            },
            {
                'name': 'clear_cache',
                'params': [],
                'purpose': 'Vide le cache',
                'body': 'self.cache.clear()'
            }
        ]
    )
    
    print("\n" + "─" * 80)
    print(class_code)
    print("─" * 80)


async def demo_experience_learning():
    """Démonstration d'apprentissage par expérience"""
    print("\n" + "=" * 80)
    print("DÉMONSTRATION 4: APPRENTISSAGE PAR EXPÉRIENCE")
    print("=" * 80 + "\n")
    
    manager = ExperienceManager(strategy=LearningStrategy.PATTERN_EXTRACTION)
    
    # Enregistrer plusieurs expériences
    print("📚 Enregistrement d'expériences...")
    
    experiences = [
        {
            'problem_type': 'data_analysis',
            'description': 'Analyser 10K lignes CSV',
            'approach': 'pandas_sequential',
            'success': True,
            'time': 2.5,
            'complexity': 4
        },
        {
            'problem_type': 'data_analysis',
            'description': 'Analyser 100K lignes CSV',
            'approach': 'pandas_sequential',
            'success': False,
            'time': 30.0,
            'complexity': 6
        },
        {
            'problem_type': 'data_analysis',
            'description': 'Analyser 100K lignes CSV',
            'approach': 'pandas_parallel',
            'success': True,
            'time': 8.5,
            'complexity': 6
        },
        {
            'problem_type': 'optimization',
            'description': 'Optimiser requête SQL',
            'approach': 'add_indexes',
            'success': True,
            'time': 1.2,
            'complexity': 5
        },
        {
            'problem_type': 'data_analysis',
            'description': 'Analyser 1M lignes CSV',
            'approach': 'pandas_parallel',
            'success': True,
            'time': 15.0,
            'complexity': 8
        }
    ]
    
    for exp_data in experiences:
        exp = await manager.record_experience(
            problem_type=exp_data['problem_type'],
            problem_description=exp_data['description'],
            solution_approach=exp_data['approach'],
            success=exp_data['success'],
            execution_time=exp_data['time'],
            complexity=exp_data['complexity']
        )
        
        status = "✓" if exp.success else "✗"
        print(f"   {status} {exp.problem_type}: {exp.solution_approach} "
              f"({exp.execution_time:.1f}s, complexité {exp.complexity})")
    
    # Recommander une approche
    print("\n💡 Recommandation pour un nouveau problème...")
    recommendation = await manager.recommend_approach(
        problem_type='data_analysis',
        complexity=7
    )
    
    if recommendation:
        print(f"   Approche recommandée: {recommendation['approach']}")
        print(f"   Confiance: {recommendation['confidence']:.0%}")
        print(f"   Temps estimé: {recommendation['estimated_time']:.1f}s")
        print(f"   Basé sur: {recommendation['based_on_experiences']} expériences")
    
    # Meilleures pratiques
    print("\n📋 Meilleures pratiques pour 'data_analysis':")
    practices = await manager.get_best_practices('data_analysis')
    for practice in practices[:3]:
        print(f"   • {practice}")
    
    # Statistiques
    print("\n📊 Statistiques d'apprentissage:")
    stats = manager.get_statistics()
    print(f"   Expériences totales: {stats['total_experiences']}")
    print(f"   Taux de succès global: {stats['success_rate']:.0%}")
    print(f"   Patterns découverts: {stats['patterns_discovered']}")
    print(f"   Complexité moyenne: {stats['average_complexity']:.1f}")


async def demo_integrated_workflow():
    """Workflow intégré: du problème à la solution"""
    print("\n" + "=" * 80)
    print("DÉMONSTRATION 5: WORKFLOW INTÉGRÉ COMPLET")
    print("=" * 80 + "\n")
    
    print("🎯 Scénario: Optimiser le calcul de statistiques sur un grand dataset\n")
    
    # 1. Définir le problème
    print("1️⃣  Définition du problème")
    problem = Problem(
        id="opt_stats_001",
        description="Calculer moyenne, médiane, écart-type sur 500K lignes",
        category="optimization",
        complexity=6,
        constraints={'max_time': '10s', 'memory': '128MB'},
        success_criteria=["Temps < 10s", "Résultats corrects"]
    )
    print(f"   ✓ Problème défini: complexité {problem.complexity}")
    
    # 2. Apprendre des expériences passées
    print("\n2️⃣  Consultation des expériences")
    exp_manager = ExperienceManager()
    
    # Simuler quelques expériences passées
    await exp_manager.record_experience(
        'optimization', 'Stats sur 100K lignes', 'numpy_vectorized',
        True, 2.0, 4
    )
    
    recommendation = await exp_manager.recommend_approach(
        'optimization', 6
    )
    
    if recommendation:
        print(f"   ✓ Approche recommandée: {recommendation['approach']}")
        print(f"   ✓ Confiance: {recommendation['confidence']:.0%}")
    
    # 3. Planifier la solution
    print("\n3️⃣  Planification de la solution")
    solver = ProblemSolver()
    steps = await solver.decompose_problem(problem, DecompositionStrategy.SEQUENTIAL)
    print(f"   ✓ Plan créé avec {len(steps)} étapes")
    
    # 4. Générer le code
    print("\n4️⃣  Génération du code")
    generator = CodeGenerator()
    
    code = await generator.generate_function(
        name="calculate_statistics",
        purpose="Calcule les statistiques sur un dataset",
        inputs=[
            {'name': 'data', 'type': 'List[float]', 'description': 'Données numériques'}
        ],
        output_type="Dict[str, float]",
        logic="""import statistics
    return {
        'mean': statistics.mean(data),
        'median': statistics.median(data),
        'stdev': statistics.stdev(data) if len(data) > 1 else 0.0
    }"""
    )
    
    print("   ✓ Code généré")
    
    # 5. Exécuter et tester
    print("\n5️⃣  Exécution et test")
    executor = CodeExecutor(SecurityLevel.MEDIUM)
    
    test_code = code + """

# Test avec des données
test_data = list(range(1, 101))
result = calculate_statistics(test_data)
print(f"Moyenne: {result['mean']}")
print(f"Médiane: {result['median']}")
print(f"Écart-type: {result['stdev']:.2f}")
"""
    
    result = await executor.execute_python(test_code)
    print(f"   ✓ Exécution: {result.success}")
    print(f"   ✓ Temps: {result.execution_time:.3f}s")
    if result.output:
        for line in result.output.strip().split('\n'):
            print(f"      {line}")
    
    # 6. Enregistrer l'expérience
    print("\n6️⃣  Enregistrement de l'expérience")
    await exp_manager.record_experience(
        problem_type='optimization',
        problem_description=problem.description,
        solution_approach='statistics_module',
        success=result.success,
        execution_time=result.execution_time,
        complexity=problem.complexity,
        lessons=['Le module statistics est efficace pour < 1M valeurs']
    )
    
    print("   ✓ Expérience enregistrée pour apprentissage futur")
    
    print("\n✅ Workflow complet terminé!")


async def main():
    """Fonction principale"""
    print("\n" + "╔" + "═" * 78 + "╗")
    print("║" + " " * 18 + "HOPPER REASONING & PLANNING SYSTEM" + " " * 26 + "║")
    print("║" + " " * 12 + "Planification, Codage et Résolution de Problèmes" + " " * 18 + "║")
    print("╚" + "═" * 78 + "╝")
    
    try:
        await demo_problem_solving()
        await demo_code_execution()
        await demo_code_generation()
        await demo_experience_learning()
        await demo_integrated_workflow()
        
        print("\n" + "=" * 80)
        print("RÉSUMÉ DES CAPACITÉS")
        print("=" * 80)
        print("""
✅ Planification avancée:
   • Décomposition hiérarchique de problèmes complexes
   • 5 stratégies de résolution (séquentiel, parallèle, itératif...)
   • Gestion des dépendances entre étapes
   • Ajustement dynamique du plan

✅ Exécution sécurisée:
   • Sandbox Python isolé
   • Limites de ressources (CPU, mémoire, temps)
   • 5 niveaux de sécurité
   • Validation du code avant exécution
   • Historique et statistiques

✅ Génération de code:
   • Templates intelligents
   • Documentation automatique
   • Tests générés
   • 4 niveaux de qualité
   • Support multi-langage

✅ Apprentissage par expérience:
   • Mémorisation des solutions
   • Extraction de patterns
   • Recommandations basées sur l'historique
   • Amélioration continue
   • Meilleures pratiques

🎯 HOPPER peut maintenant planifier, coder et résoudre des problèmes complexes
   de manière autonome tout en apprenant de ses expériences!
""")
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
