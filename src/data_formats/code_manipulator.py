"""
Manipulateur de code source HOPPER
Parse, analyse et modifie du code de manière sécurisée
"""

import ast
import re
import json
from pathlib import Path
from typing import Dict, Any, Optional, Union, List, Tuple
from dataclasses import dataclass
from enum import Enum


class CodeLanguage(Enum):
    """Langages de programmation supportés"""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JSON = "json"
    YAML = "yaml"
    HTML = "html"
    CSS = "css"
    MARKDOWN = "markdown"
    UNKNOWN = "unknown"


@dataclass
class CodeAnalysis:
    """Résultat d'analyse de code"""
    language: CodeLanguage
    syntax_valid: bool
    functions: List[Dict[str, Any]]
    classes: List[Dict[str, Any]]
    imports: List[str]
    variables: List[str]
    comments: List[str]
    complexity: int
    lines_of_code: int
    errors: List[str]


@dataclass
class CodeModification:
    """Modification à appliquer au code"""
    operation: str  # rename, extract_method, add_comment, format, etc.
    target: str  # Nom de la fonction/classe/variable
    new_value: Any  # Nouvelle valeur ou paramètres
    line_number: Optional[int] = None


@dataclass
class CodeFormat:
    """Configuration de formatage de code"""
    language: CodeLanguage
    indent_size: int = 4
    use_tabs: bool = False
    line_length: int = 88
    quote_style: str = "double"  # single, double
    trailing_comma: bool = True
    semicolons: bool = True  # Pour JS/TS


class CodeManipulator:
    """Manipulateur de code source"""
    
    def __init__(self):
        self.language_patterns = {
            CodeLanguage.PYTHON: [r'\.py$', r'def\s+\w+', r'class\s+\w+', r'import\s+\w+'],
            CodeLanguage.JAVASCRIPT: [r'\.js$', r'function\s+\w+', r'const\s+\w+\s*=', r'let\s+\w+'],
            CodeLanguage.TYPESCRIPT: [r'\.ts$', r'interface\s+\w+', r'type\s+\w+', r':\s*\w+'],
            CodeLanguage.JSON: [r'\.json$'],
            CodeLanguage.YAML: [r'\.ya?ml$'],
            CodeLanguage.HTML: [r'\.html?$', r'<\w+[^>]*>'],
            CodeLanguage.CSS: [r'\.css$', r'\w+\s*{'],
            CodeLanguage.MARKDOWN: [r'\.md$', r'^#+\s+']
        }
    
    def detect_language(
        self,
        file_path: Optional[Union[str, Path]] = None,
        code: Optional[str] = None
    ) -> CodeLanguage:
        """Détecte le langage du code"""
        if file_path:
            file_path = Path(file_path)
            extension = file_path.suffix.lower()
            
            if extension == '.py':
                return CodeLanguage.PYTHON
            elif extension in ['.js', '.jsx']:
                return CodeLanguage.JAVASCRIPT
            elif extension in ['.ts', '.tsx']:
                return CodeLanguage.TYPESCRIPT
            elif extension == '.json':
                return CodeLanguage.JSON
            elif extension in ['.yaml', '.yml']:
                return CodeLanguage.YAML
            elif extension in ['.html', '.htm']:
                return CodeLanguage.HTML
            elif extension == '.css':
                return CodeLanguage.CSS
            elif extension == '.md':
                return CodeLanguage.MARKDOWN
        
        if code:
            # Analyse du contenu
            for lang, patterns in self.language_patterns.items():
                matches = sum(1 for pattern in patterns if re.search(pattern, code, re.MULTILINE))
                if matches >= 2:
                    return lang
        
        return CodeLanguage.UNKNOWN
    
    async def analyze_code(
        self,
        file_path: Union[str, Path],
        language: Optional[CodeLanguage] = None
    ) -> CodeAnalysis:
        """
        Analyse un fichier de code source
        
        Args:
            file_path: Chemin du fichier
            language: Langage (détecté automatiquement si None)
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Fichier non trouvé: {file_path}")
        
        code = file_path.read_text(encoding='utf-8')
        
        if language is None:
            language = self.detect_language(file_path=file_path, code=code)
        
        if language == CodeLanguage.PYTHON:
            return await self._analyze_python(code)
        elif language == CodeLanguage.JAVASCRIPT:
            return await self._analyze_javascript(code)
        elif language == CodeLanguage.JSON:
            return await self._analyze_json(code)
        else:
            # Analyse générique
            return await self._analyze_generic(code, language)
    
    async def _analyze_python(self, code: str) -> CodeAnalysis:
        """Analyse du code Python avec AST"""
        functions = []
        classes = []
        imports = []
        variables = []
        comments = []
        errors = []
        
        # Extraire les commentaires
        for match in re.finditer(r'#(.+)$', code, re.MULTILINE):
            comments.append(match.group(1).strip())
        
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                # Fonctions
                if isinstance(node, ast.FunctionDef):
                    functions.append({
                        'name': node.name,
                        'line': node.lineno,
                        'args': [arg.arg for arg in node.args.args],
                        'decorators': [ast.unparse(d) for d in node.decorator_list] if hasattr(ast, 'unparse') else [],
                        'docstring': ast.get_docstring(node)
                    })
                
                # Classes
                elif isinstance(node, ast.ClassDef):
                    methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                    classes.append({
                        'name': node.name,
                        'line': node.lineno,
                        'methods': methods,
                        'bases': [ast.unparse(base) if hasattr(ast, 'unparse') else '' for base in node.bases],
                        'docstring': ast.get_docstring(node)
                    })
                
                # Imports
                elif isinstance(node, ast.Import):
                    for name in node.names:
                        imports.append(name.name)
                
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ''
                    for name in node.names:
                        imports.append(f"{module}.{name.name}")
                
                # Variables globales
                elif isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            variables.append(target.id)
            
            syntax_valid = True
            
        except SyntaxError as e:
            syntax_valid = False
            errors.append(f"Erreur de syntaxe ligne {e.lineno}: {e.msg}")
        
        # Calcul de la complexité cyclomatique approximative
        complexity = self._calculate_complexity_python(code)
        
        # Lignes de code (sans commentaires et lignes vides)
        loc = len([line for line in code.split('\n') 
                  if line.strip() and not line.strip().startswith('#')])
        
        return CodeAnalysis(
            language=CodeLanguage.PYTHON,
            syntax_valid=syntax_valid,
            functions=functions,
            classes=classes,
            imports=list(set(imports)),
            variables=list(set(variables)),
            comments=comments,
            complexity=complexity,
            lines_of_code=loc,
            errors=errors
        )
    
    async def _analyze_javascript(self, code: str) -> CodeAnalysis:
        """Analyse basique du code JavaScript"""
        functions = []
        classes = []
        imports = []
        variables = []
        comments = []
        
        # Commentaires
        for match in re.finditer(r'//(.+)$|/\*(.+?)\*/', code, re.MULTILINE | re.DOTALL):
            comment = match.group(1) or match.group(2)
            if comment:
                comments.append(comment.strip())
        
        # Fonctions
        for match in re.finditer(
            r'(?:function\s+(\w+)|const\s+(\w+)\s*=\s*(?:async\s+)?(?:function|\([^)]*\)\s*=>))',
            code
        ):
            func_name = match.group(1) or match.group(2)
            if func_name:
                functions.append({
                    'name': func_name,
                    'line': code[:match.start()].count('\n') + 1
                })
        
        # Classes
        for match in re.finditer(r'class\s+(\w+)', code):
            classes.append({
                'name': match.group(1),
                'line': code[:match.start()].count('\n') + 1
            })
        
        # Imports
        for match in re.finditer(r'import\s+.+?\s+from\s+[\'"](.+?)[\'"]', code):
            imports.append(match.group(1))
        
        # Variables
        for match in re.finditer(r'(?:const|let|var)\s+(\w+)', code):
            variables.append(match.group(1))
        
        complexity = code.count('if') + code.count('for') + code.count('while') + code.count('case')
        loc = len([line for line in code.split('\n') if line.strip() and not line.strip().startswith('//')])
        
        return CodeAnalysis(
            language=CodeLanguage.JAVASCRIPT,
            syntax_valid=True,
            functions=functions,
            classes=classes,
            imports=list(set(imports)),
            variables=list(set(variables)),
            comments=comments,
            complexity=complexity,
            lines_of_code=loc,
            errors=[]
        )
    
    async def _analyze_json(self, code: str) -> CodeAnalysis:
        """Analyse JSON"""
        errors = []
        syntax_valid = True
        
        try:
            json.loads(code)
        except json.JSONDecodeError as e:
            syntax_valid = False
            errors.append(f"JSON invalide: {e.msg} (ligne {e.lineno})")
        
        return CodeAnalysis(
            language=CodeLanguage.JSON,
            syntax_valid=syntax_valid,
            functions=[],
            classes=[],
            imports=[],
            variables=[],
            comments=[],
            complexity=0,
            lines_of_code=len(code.split('\n')),
            errors=errors
        )
    
    async def _analyze_generic(self, code: str, language: CodeLanguage) -> CodeAnalysis:
        """Analyse générique pour langages non supportés"""
        comments = []
        
        # Détecter les commentaires courants
        for match in re.finditer(r'(?://|#|/\*|\*)(.+?)(?:\*/|$)', code, re.MULTILINE):
            comments.append(match.group(1).strip())
        
        loc = len([line for line in code.split('\n') if line.strip()])
        
        return CodeAnalysis(
            language=language,
            syntax_valid=True,
            functions=[],
            classes=[],
            imports=[],
            variables=[],
            comments=comments,
            complexity=0,
            lines_of_code=loc,
            errors=[]
        )
    
    def _calculate_complexity_python(self, code: str) -> int:
        """Calcule la complexité cyclomatique approximative"""
        try:
            tree = ast.parse(code)
            complexity = 1  # Complexité de base
            
            for node in ast.walk(tree):
                # +1 pour chaque branche
                if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                    complexity += 1
                elif isinstance(node, ast.BoolOp):
                    complexity += len(node.values) - 1
            
            return complexity
        except:
            return 0
    
    async def modify_code(
        self,
        file_path: Union[str, Path],
        modifications: List[CodeModification],
        create_backup: bool = True
    ) -> Tuple[bool, str]:
        """
        Applique des modifications au code
        
        Args:
            file_path: Fichier à modifier
            modifications: Liste des modifications
            create_backup: Créer une sauvegarde
            
        Returns:
            (succès, message)
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            return False, f"Fichier non trouvé: {file_path}"
        
        # Backup
        if create_backup:
            backup_path = file_path.with_suffix(file_path.suffix + '.bak')
            backup_path.write_bytes(file_path.read_bytes())
        
        try:
            code = file_path.read_text(encoding='utf-8')
            
            for mod in modifications:
                if mod.operation == 'rename':
                    code = await self._rename_symbol(code, mod.target, mod.new_value)
                elif mod.operation == 'add_comment':
                    code = await self._add_comment(code, mod.target, mod.new_value, mod.line_number)
                elif mod.operation == 'remove_unused_imports':
                    code = await self._remove_unused_imports(code)
                elif mod.operation == 'format':
                    code = await self._format_code(code, mod.new_value)
            
            # Valider le code modifié
            language = self.detect_language(file_path=file_path)
            if language == CodeLanguage.PYTHON:
                try:
                    ast.parse(code)
                except SyntaxError as e:
                    return False, f"Code invalide après modifications: {e}"
            
            # Sauvegarder
            file_path.write_text(code, encoding='utf-8')
            
            return True, f"{len(modifications)} modification(s) appliquée(s)"
            
        except Exception as e:
            if create_backup and backup_path.exists():
                file_path.write_bytes(backup_path.read_bytes())
            return False, f"Erreur: {e}"
    
    async def _rename_symbol(self, code: str, old_name: str, new_name: str) -> str:
        """Renomme un symbole (variable, fonction, classe)"""
        # Utiliser des regex avec word boundaries
        pattern = r'\b' + re.escape(old_name) + r'\b'
        return re.sub(pattern, new_name, code)
    
    async def _add_comment(
        self,
        code: str,
        target: str,
        comment: str,
        line_number: Optional[int]
    ) -> str:
        """Ajoute un commentaire"""
        lines = code.split('\n')
        
        if line_number is not None:
            # Commentaire à une ligne spécifique
            if 0 <= line_number < len(lines):
                indent = len(lines[line_number]) - len(lines[line_number].lstrip())
                lines.insert(line_number, ' ' * indent + f"# {comment}")
        else:
            # Commentaire avant une fonction/classe
            for i, line in enumerate(lines):
                if re.search(rf'\b(?:def|class)\s+{re.escape(target)}\b', line):
                    indent = len(line) - len(line.lstrip())
                    lines.insert(i, ' ' * indent + f"# {comment}")
                    break
        
        return '\n'.join(lines)
    
    async def _remove_unused_imports(self, code: str) -> str:
        """Retire les imports non utilisés (Python)"""
        try:
            tree = ast.parse(code)
            
            # Collecter tous les imports
            imports = {}
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for name in node.names:
                        imports[name.name] = node.lineno
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ''
                    for name in node.names:
                        imports[f"{module}.{name.name}"] = node.lineno
            
            # Vérifier l'utilisation
            used_imports = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Name):
                    for imp in imports.keys():
                        if imp.split('.')[-1] == node.id:
                            used_imports.add(imp)
            
            # Retirer les imports non utilisés
            lines = code.split('\n')
            unused_lines = set()
            
            for imp, line_no in imports.items():
                if imp not in used_imports:
                    unused_lines.add(line_no - 1)
            
            cleaned_lines = [line for i, line in enumerate(lines) if i not in unused_lines]
            
            return '\n'.join(cleaned_lines)
            
        except:
            return code
    
    async def _format_code(self, code: str, style: Dict[str, Any]) -> str:
        """Formate le code selon un style"""
        # Formatage basique
        lines = code.split('\n')
        
        # Retirer les lignes vides excessives
        formatted = []
        prev_empty = False
        
        for line in lines:
            is_empty = not line.strip()
            
            if is_empty:
                if not prev_empty:
                    formatted.append(line)
                prev_empty = True
            else:
                formatted.append(line)
                prev_empty = False
        
        return '\n'.join(formatted)
    
    async def extract_function(
        self,
        file_path: Union[str, Path],
        start_line: int,
        end_line: int,
        function_name: str
    ) -> Tuple[bool, str]:
        """
        Extrait un bloc de code dans une nouvelle fonction
        
        Args:
            file_path: Fichier source
            start_line: Ligne de début
            end_line: Ligne de fin
            function_name: Nom de la nouvelle fonction
        """
        file_path = Path(file_path)
        code = file_path.read_text(encoding='utf-8')
        lines = code.split('\n')
        
        if not (0 <= start_line < end_line <= len(lines)):
            return False, "Numéros de ligne invalides"
        
        # Extraire le bloc
        extracted = lines[start_line:end_line]
        
        # Déterminer l'indentation
        indent = min(len(line) - len(line.lstrip()) for line in extracted if line.strip())
        
        # Créer la fonction
        new_function = [
            f"def {function_name}():",
            *[' ' * 4 + line[indent:] for line in extracted]
        ]
        
        # Remplacer dans le code
        lines[start_line:end_line] = [' ' * indent + f"{function_name}()"]
        
        # Insérer la nouvelle fonction avant
        lines[start_line:start_line] = new_function + ['']
        
        # Sauvegarder
        new_code = '\n'.join(lines)
        
        try:
            ast.parse(new_code)
            file_path.write_text(new_code, encoding='utf-8')
            return True, f"Fonction {function_name} créée"
        except SyntaxError as e:
            return False, f"Code invalide: {e}"
    
    async def add_docstring(
        self,
        file_path: Union[str, Path],
        target: str,
        docstring: str
    ) -> Tuple[bool, str]:
        """Ajoute une docstring à une fonction/classe"""
        file_path = Path(file_path)
        code = file_path.read_text(encoding='utf-8')
        lines = code.split('\n')
        
        # Trouver la fonction/classe
        for i, line in enumerate(lines):
            if re.search(rf'\b(?:def|class)\s+{re.escape(target)}\b', line):
                # Vérifier si docstring existe déjà
                next_line = i + 1
                if next_line < len(lines):
                    if '"""' in lines[next_line] or "'''" in lines[next_line]:
                        return False, "Docstring existe déjà"
                
                # Ajouter la docstring
                indent = len(line) - len(line.lstrip()) + 4
                docstring_lines = [
                    ' ' * indent + '"""',
                    ' ' * indent + docstring,
                    ' ' * indent + '"""'
                ]
                
                lines[next_line:next_line] = docstring_lines
                
                # Sauvegarder
                new_code = '\n'.join(lines)
                file_path.write_text(new_code, encoding='utf-8')
                
                return True, f"Docstring ajoutée à {target}"
        
        return False, f"Fonction/classe {target} non trouvée"
