"""
Sandbox d'exécution sécurisé HOPPER
Exécute du code en toute sécurité avec limites de ressources
"""

import asyncio
import subprocess
import tempfile
import resource
import signal
import sys
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum
from pathlib import Path
from datetime import datetime
import json


class SecurityLevel(Enum):
    """Niveaux de sécurité pour l'exécution"""
    UNRESTRICTED = "unrestricted"  # Pas de restrictions (dangereux!)
    LOW = "low"  # Restrictions basiques
    MEDIUM = "medium"  # Restrictions modérées
    HIGH = "high"  # Restrictions strictes
    PARANOID = "paranoid"  # Isolation maximale


class ExecutionEnvironment(Enum):
    """Environnements d'exécution disponibles"""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    SHELL = "shell"
    SQL = "sql"


@dataclass
class ExecutionResult:
    """Résultat d'une exécution de code"""
    success: bool
    output: str
    error: Optional[str] = None
    exit_code: int = 0
    execution_time: float = 0.0
    memory_used: int = 0  # En bytes
    stdout: str = ""
    stderr: str = ""
    return_value: Optional[Any] = None
    warnings: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire"""
        return {
            'success': self.success,
            'output': self.output,
            'error': self.error,
            'exit_code': self.exit_code,
            'execution_time': self.execution_time,
            'memory_used': self.memory_used,
            'stdout': self.stdout,
            'stderr': self.stderr,
            'return_value': str(self.return_value) if self.return_value else None,
            'warnings': self.warnings
        }


class CodeExecutor:
    """
    Sandbox d'exécution sécurisé
    Exécute du code avec isolation et limites de ressources
    """
    
    def __init__(self, security_level: SecurityLevel = SecurityLevel.HIGH):
        self.security_level = security_level
        self.execution_history: List[ExecutionResult] = []
        self.resource_limits = self._init_resource_limits()
        self.blocked_imports = self._init_blocked_imports()
        self.allowed_builtins = self._init_allowed_builtins()
        
    def _init_resource_limits(self) -> Dict[str, Any]:
        """Initialise les limites de ressources selon le niveau de sécurité"""
        limits = {
            SecurityLevel.UNRESTRICTED: {
                'timeout': None,
                'max_memory': None,
                'max_cpu_time': None,
                'max_file_size': None
            },
            SecurityLevel.LOW: {
                'timeout': 60.0,  # 60 secondes
                'max_memory': 512 * 1024 * 1024,  # 512 MB
                'max_cpu_time': 30.0,
                'max_file_size': 10 * 1024 * 1024  # 10 MB
            },
            SecurityLevel.MEDIUM: {
                'timeout': 30.0,
                'max_memory': 256 * 1024 * 1024,  # 256 MB
                'max_cpu_time': 15.0,
                'max_file_size': 5 * 1024 * 1024
            },
            SecurityLevel.HIGH: {
                'timeout': 10.0,
                'max_memory': 128 * 1024 * 1024,  # 128 MB
                'max_cpu_time': 5.0,
                'max_file_size': 1 * 1024 * 1024
            },
            SecurityLevel.PARANOID: {
                'timeout': 5.0,
                'max_memory': 64 * 1024 * 1024,  # 64 MB
                'max_cpu_time': 2.0,
                'max_file_size': 512 * 1024
            }
        }
        
        return limits[self.security_level]
    
    def _init_blocked_imports(self) -> List[str]:
        """Modules dangereux à bloquer"""
        if self.security_level in [SecurityLevel.UNRESTRICTED, SecurityLevel.LOW]:
            return []
        
        # Modules potentiellement dangereux
        dangerous = [
            'os',
            'subprocess',
            'sys',
            'socket',
            'urllib',
            'requests',
            'multiprocessing',
            '__import__',
            'eval',
            'exec',
            'compile',
            'open'  # Fichiers
        ]
        
        if self.security_level == SecurityLevel.PARANOID:
            dangerous.extend([
                'pathlib',
                'tempfile',
                'shutil',
                'glob',
                'pickle',
                'marshal'
            ])
        
        return dangerous
    
    def _init_allowed_builtins(self) -> Dict[str, Any]:
        """Builtins autorisés selon le niveau de sécurité"""
        # Builtins sûrs de base
        safe_builtins = {
            'abs': abs,
            'all': all,
            'any': any,
            'bool': bool,
            'dict': dict,
            'enumerate': enumerate,
            'filter': filter,
            'float': float,
            'int': int,
            'isinstance': isinstance,
            'len': len,
            'list': list,
            'map': map,
            'max': max,
            'min': min,
            'print': print,
            'range': range,
            'reversed': reversed,
            'set': set,
            'sorted': sorted,
            'str': str,
            'sum': sum,
            'tuple': tuple,
            'type': type,
            'zip': zip
        }
        
        if self.security_level in [SecurityLevel.UNRESTRICTED, SecurityLevel.LOW]:
            # Ajouter plus de builtins
            safe_builtins.update({
                'open': open,
                'input': input,
                'help': help
            })
        
        return safe_builtins
    
    async def execute_python(
        self,
        code: str,
        globals_dict: Optional[Dict[str, Any]] = None,
        locals_dict: Optional[Dict[str, Any]] = None
    ) -> ExecutionResult:
        """
        Exécute du code Python de manière sécurisée
        
        Args:
            code: Le code Python à exécuter
            globals_dict: Variables globales (optionnel)
            locals_dict: Variables locales (optionnel)
            
        Returns:
            Résultat de l'exécution
        """
        start_time = datetime.now()
        result = ExecutionResult(success=False, output="")
        
        try:
            # Validation du code
            validation = self._validate_code(code)
            if not validation['safe']:
                result.error = f"Code dangereux détecté: {validation['reason']}"
                result.warnings = validation['warnings']
                return result
            
            # Préparer l'environnement
            safe_globals = globals_dict or {}
            safe_globals['__builtins__'] = self.allowed_builtins
            safe_locals = locals_dict or {}
            
            # Capturer la sortie
            from io import StringIO
            import sys
            
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            sys.stdout = StringIO()
            sys.stderr = StringIO()
            
            try:
                # Définir les limites de ressources
                self._set_resource_limits()
                
                # Exécuter avec timeout
                if self.resource_limits['timeout']:
                    # Utiliser asyncio.wait_for pour le timeout
                    await asyncio.wait_for(
                        self._run_code_async(code, safe_globals, safe_locals),
                        timeout=self.resource_limits['timeout']
                    )
                else:
                    # Pas de timeout
                    exec(code, safe_globals, safe_locals)
                
                # Récupérer la sortie
                result.stdout = sys.stdout.getvalue()
                result.stderr = sys.stderr.getvalue()
                result.output = result.stdout
                
                # Récupérer la valeur de retour si disponible
                if 'result' in safe_locals:
                    result.return_value = safe_locals['result']
                
                result.success = True
                result.exit_code = 0
                
            except asyncio.TimeoutError:
                result.error = f"Timeout dépassé ({self.resource_limits['timeout']}s)"
                result.exit_code = 124  # Code timeout standard
            except MemoryError:
                result.error = "Limite de mémoire dépassée"
                result.exit_code = 137  # SIGKILL
            except Exception as e:
                result.error = f"Erreur d'exécution: {str(e)}"
                result.stderr = sys.stderr.getvalue()
                result.exit_code = 1
            finally:
                # Restaurer stdout/stderr
                sys.stdout = old_stdout
                sys.stderr = old_stderr
        
        except Exception as e:
            result.error = f"Erreur de préparation: {str(e)}"
            result.exit_code = 2
        
        # Calculer le temps d'exécution
        end_time = datetime.now()
        result.execution_time = (end_time - start_time).total_seconds()
        
        # Sauvegarder dans l'historique
        self.execution_history.append(result)
        
        return result
    
    async def _run_code_async(self, code: str, globals_dict: Dict, locals_dict: Dict):
        """Wrapper async pour exec()"""
        exec(code, globals_dict, locals_dict)
    
    def _validate_code(self, code: str) -> Dict[str, Any]:
        """Valide que le code est sûr"""
        warnings = []
        
        # Vérifier les imports bloqués
        for blocked in self.blocked_imports:
            if f"import {blocked}" in code or f"from {blocked}" in code:
                return {
                    'safe': False,
                    'reason': f"Import interdit: {blocked}",
                    'warnings': warnings
                }
        
        # Vérifier les fonctions dangereuses
        dangerous_funcs = ['eval', 'exec', 'compile', '__import__']
        for func in dangerous_funcs:
            if func in code and self.security_level != SecurityLevel.UNRESTRICTED:
                return {
                    'safe': False,
                    'reason': f"Fonction interdite: {func}",
                    'warnings': warnings
                }
        
        # Vérifications supplémentaires
        if 'while True' in code:
            warnings.append("Boucle infinie potentielle détectée")
        
        if 'recursion' in code.lower():
            warnings.append("Récursion détectée - risque de stack overflow")
        
        return {
            'safe': True,
            'reason': None,
            'warnings': warnings
        }
    
    def _set_resource_limits(self):
        """Définit les limites de ressources système"""
        if sys.platform == 'win32':
            # Windows ne supporte pas resource.setrlimit
            return
        
        try:
            # Limite de mémoire
            if self.resource_limits['max_memory']:
                resource.setrlimit(
                    resource.RLIMIT_AS,
                    (self.resource_limits['max_memory'], self.resource_limits['max_memory'])
                )
            
            # Limite de temps CPU
            if self.resource_limits['max_cpu_time']:
                resource.setrlimit(
                    resource.RLIMIT_CPU,
                    (int(self.resource_limits['max_cpu_time']),
                     int(self.resource_limits['max_cpu_time']))
                )
        except Exception:
            # Silently fail si les limites ne peuvent être définies
            pass
    
    async def execute_shell(self, command: str) -> ExecutionResult:
        """
        Exécute une commande shell de manière sécurisée
        
        Args:
            command: Commande à exécuter
            
        Returns:
            Résultat de l'exécution
        """
        result = ExecutionResult(success=False, output="")
        
        # Validation de sécurité
        if self.security_level in [SecurityLevel.HIGH, SecurityLevel.PARANOID]:
            result.error = "Exécution shell interdite en mode haute sécurité"
            return result
        
        # Commandes dangereuses
        dangerous = ['rm ', 'del ', 'format', 'dd ', 'mkfs', '> /dev/']
        for danger in dangerous:
            if danger in command.lower():
                result.error = f"Commande dangereuse détectée: {danger}"
                return result
        
        start_time = datetime.now()
        
        try:
            # Exécuter avec subprocess
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                shell=True
            )
            
            # Attendre avec timeout
            timeout = self.resource_limits['timeout'] or 30.0
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
            
            result.stdout = stdout.decode('utf-8', errors='replace')
            result.stderr = stderr.decode('utf-8', errors='replace')
            result.output = result.stdout
            result.exit_code = process.returncode if process.returncode is not None else -1
            result.success = process.returncode == 0
            
        except asyncio.TimeoutError:
            result.error = f"Timeout dépassé ({timeout}s)"
            result.exit_code = 124
        except Exception as e:
            result.error = str(e)
            result.exit_code = 1
        
        end_time = datetime.now()
        result.execution_time = (end_time - start_time).total_seconds()
        
        self.execution_history.append(result)
        
        return result
    
    async def execute_in_file(
        self,
        code: str,
        language: ExecutionEnvironment = ExecutionEnvironment.PYTHON
    ) -> ExecutionResult:
        """
        Exécute du code dans un fichier temporaire
        Plus sûr que exec() direct
        
        Args:
            code: Code à exécuter
            language: Langage du code
            
        Returns:
            Résultat de l'exécution
        """
        result = ExecutionResult(success=False, output="")
        
        # Créer un fichier temporaire
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix=self._get_extension(language),
            delete=False
        ) as f:
            f.write(code)
            temp_file = f.name
        
        try:
            # Commande d'exécution selon le langage
            if language == ExecutionEnvironment.PYTHON:
                command = [sys.executable, temp_file]
            elif language == ExecutionEnvironment.JAVASCRIPT:
                command = ['node', temp_file]
            else:
                result.error = f"Langage non supporté: {language}"
                return result
            
            start_time = datetime.now()
            
            # Exécuter
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            timeout = self.resource_limits['timeout'] or 30.0
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
            
            result.stdout = stdout.decode('utf-8', errors='replace')
            result.stderr = stderr.decode('utf-8', errors='replace')
            result.output = result.stdout
            result.exit_code = process.returncode if process.returncode is not None else -1
            result.success = process.returncode == 0
            
            end_time = datetime.now()
            result.execution_time = (end_time - start_time).total_seconds()
            
        except asyncio.TimeoutError:
            result.error = f"Timeout dépassé ({timeout}s)"
            result.exit_code = 124
        except Exception as e:
            result.error = str(e)
            result.exit_code = 1
        finally:
            # Nettoyer le fichier temporaire
            try:
                Path(temp_file).unlink()
            except:
                pass
        
        self.execution_history.append(result)
        
        return result
    
    def _get_extension(self, language: ExecutionEnvironment) -> str:
        """Retourne l'extension de fichier pour un langage"""
        extensions = {
            ExecutionEnvironment.PYTHON: '.py',
            ExecutionEnvironment.JAVASCRIPT: '.js',
            ExecutionEnvironment.SHELL: '.sh',
            ExecutionEnvironment.SQL: '.sql'
        }
        return extensions.get(language, '.txt')
    
    async def test_code(self, code: str, test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Teste du code avec plusieurs cas de test
        
        Args:
            code: Code à tester
            test_cases: Liste de cas de test {'input': ..., 'expected': ...}
            
        Returns:
            Résultats des tests
        """
        results = {
            'total': len(test_cases),
            'passed': 0,
            'failed': 0,
            'errors': 0,
            'details': []
        }
        
        for i, test in enumerate(test_cases):
            # Préparer le code avec le test
            test_code = code + f"\nresult = test({test['input']})"
            
            # Exécuter
            exec_result = await self.execute_python(test_code)
            
            # Vérifier le résultat
            test_result = {
                'test_id': i + 1,
                'input': test['input'],
                'expected': test['expected'],
                'actual': exec_result.return_value,
                'passed': False,
                'error': exec_result.error
            }
            
            if exec_result.success:
                if exec_result.return_value == test['expected']:
                    test_result['passed'] = True
                    results['passed'] += 1
                else:
                    results['failed'] += 1
            else:
                results['errors'] += 1
            
            results['details'].append(test_result)
        
        results['success_rate'] = results['passed'] / results['total'] if results['total'] > 0 else 0
        
        return results
    
    def get_history(self, limit: int = 10) -> List[ExecutionResult]:
        """Récupère l'historique d'exécution"""
        return self.execution_history[-limit:]
    
    def clear_history(self):
        """Efface l'historique"""
        self.execution_history.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Statistiques d'utilisation"""
        if not self.execution_history:
            return {
                'total_executions': 0,
                'success_rate': 0,
                'average_time': 0,
                'total_time': 0
            }
        
        total = len(self.execution_history)
        successes = sum(1 for r in self.execution_history if r.success)
        times = [r.execution_time for r in self.execution_history]
        
        return {
            'total_executions': total,
            'success_rate': successes / total,
            'average_time': sum(times) / len(times),
            'total_time': sum(times),
            'security_level': self.security_level.value
        }
