"""
Générateur de code intelligent HOPPER
Génère du code optimisé avec templates et tests automatiques
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum
import re


class CodeQuality(Enum):
    """Niveaux de qualité du code"""
    QUICK = "quick"  # Rapide, pas d'optimisation
    STANDARD = "standard"  # Qualité normale
    PRODUCTION = "production"  # Prêt pour la production
    ENTERPRISE = "enterprise"  # Standards enterprise


@dataclass
class GenerationConfig:
    """Configuration de génération"""
    quality: CodeQuality = CodeQuality.STANDARD
    add_comments: bool = True
    add_docstrings: bool = True
    add_type_hints: bool = True
    add_error_handling: bool = True
    add_logging: bool = False
    add_tests: bool = False
    style_guide: str = "pep8"  # pep8, google, numpy
    max_line_length: int = 88


@dataclass
class CodeTemplate:
    """Template de code"""
    name: str
    language: str
    template: str
    parameters: List[str]
    description: str
    category: str
    
    def render(self, **kwargs) -> str:
        """Rend le template avec les paramètres"""
        code = self.template
        for key, value in kwargs.items():
            code = code.replace(f"{{{{{key}}}}}", str(value))
        return code


class CodeGenerator:
    """
    Générateur de code intelligent
    Crée du code optimisé avec documentation et tests
    """
    
    def __init__(self, config: Optional[GenerationConfig] = None):
        self.config = config or GenerationConfig()
        self.templates = self._init_templates()
        self.generation_history: List[Dict[str, Any]] = []
    
    def _init_templates(self) -> Dict[str, CodeTemplate]:
        """Initialise les templates de code"""
        templates = {}
        
        # Template fonction Python
        templates['python_function'] = CodeTemplate(
            name='python_function',
            language='python',
            template='''def {{name}}({{params}}):
    """{{docstring}}"""
    {{body}}
''',
            parameters=['name', 'params', 'docstring', 'body'],
            description='Fonction Python basique',
            category='function'
        )
        
        # Template classe Python
        templates['python_class'] = CodeTemplate(
            name='python_class',
            language='python',
            template='''class {{name}}:
    """{{docstring}}"""
    
    def __init__(self{{init_params}}):
        """Initialise {{name}}"""
        {{init_body}}
    
    {{methods}}
''',
            parameters=['name', 'docstring', 'init_params', 'init_body', 'methods'],
            description='Classe Python',
            category='class'
        )
        
        # Template API REST
        templates['api_endpoint'] = CodeTemplate(
            name='api_endpoint',
            language='python',
            template='''@app.route('/{{route}}', methods=['{{method}}'])
def {{name}}():
    """{{docstring}}"""
    try:
        {{body}}
        return jsonify({{'status': 'success', 'data': result}}), 200
    except Exception as e:
        return jsonify({{'status': 'error', 'message': str(e)}}), 500
''',
            parameters=['route', 'method', 'name', 'docstring', 'body'],
            description='Endpoint API REST',
            category='api'
        )
        
        # Template data processing
        templates['data_processor'] = CodeTemplate(
            name='data_processor',
            language='python',
            template='''def process_{{name}}(data: {{input_type}}) -> {{output_type}}:
    """
    Traite les données {{name}}
    
    Args:
        data: Données d'entrée
        
    Returns:
        Données traitées
    """
    result = []
    for item in data:
        {{processing}}
        result.append(processed_item)
    
    return result
''',
            parameters=['name', 'input_type', 'output_type', 'processing'],
            description='Processeur de données',
            category='data'
        )
        
        return templates
    
    async def generate_function(
        self,
        name: str,
        purpose: str,
        inputs: List[Dict[str, str]],
        output_type: str,
        logic: Optional[str] = None
    ) -> str:
        """
        Génère une fonction complète
        
        Args:
            name: Nom de la fonction
            purpose: But de la fonction
            inputs: Liste de {'name': '', 'type': '', 'description': ''}
            output_type: Type de retour
            logic: Logique (générée si None)
        """
        # Construire la signature
        params = ", ".join([
            f"{inp['name']}: {inp['type']}" if self.config.add_type_hints
            else inp['name']
            for inp in inputs
        ])
        
        # Docstring
        docstring = purpose
        if self.config.add_docstrings:
            docstring += "\n    \n    Args:\n"
            for inp in inputs:
                docstring += f"        {inp['name']}: {inp.get('description', '')}\n"
            docstring += f"    \n    Returns:\n        {output_type}"
        
        # Corps de la fonction
        if logic is None:
            logic = self._generate_logic(purpose, inputs)
        
        # Ajouter gestion d'erreurs
        if self.config.add_error_handling:
            logic = f"""try:
        {logic}
    except Exception as e:
        raise ValueError(f"Erreur dans {name}: {{e}}")"""
        
        # Rendu
        code = self.templates['python_function'].render(
            name=name,
            params=params,
            docstring=docstring,
            body=self._indent(logic, 4)
        )
        
        # Ajouter tests si demandé
        if self.config.add_tests:
            code += "\n\n" + self._generate_tests(name, inputs, output_type)
        
        # Sauvegarder
        self.generation_history.append({
            'type': 'function',
            'name': name,
            'code': code,
            'config': self.config.__dict__
        })
        
        return code
    
    def _generate_logic(self, purpose: str, inputs: List[Dict[str, str]]) -> str:
        """Génère la logique de base d'une fonction"""
        # Logique simple basée sur le but
        if 'calculer' in purpose.lower() or 'calculate' in purpose.lower():
            return "result = " + " + ".join([inp['name'] for inp in inputs]) + "\nreturn result"
        elif 'filtrer' in purpose.lower() or 'filter' in purpose.lower():
            inp_name = inputs[0]['name'] if inputs else 'data'
            return f"return [x for x in {inp_name} if condition(x)]"
        elif 'transformer' in purpose.lower() or 'transform' in purpose.lower():
            inp_name = inputs[0]['name'] if inputs else 'data'
            return f"return [process(x) for x in {inp_name}]"
        else:
            return "# TODO: Implémenter la logique\npass"
    
    def _indent(self, code: str, spaces: int) -> str:
        """Indente du code"""
        indent = " " * spaces
        return "\n".join(indent + line if line.strip() else line 
                        for line in code.split("\n"))
    
    def _generate_tests(self, func_name: str, inputs: List[Dict[str, str]], output_type: str) -> str:
        """Génère des tests unitaires"""
        test_code = f'''def test_{func_name}():
    """Tests pour {func_name}"""
    # Test cas normal
    result = {func_name}('''
        
        # Valeurs de test
        test_values = []
        for inp in inputs:
            if 'int' in inp['type'].lower():
                test_values.append('1')
            elif 'str' in inp['type'].lower():
                test_values.append('"test"')
            elif 'list' in inp['type'].lower():
                test_values.append('[1, 2, 3]')
            else:
                test_values.append('None')
        
        test_code += ', '.join(test_values)
        test_code += ''')
    assert result is not None
    
    # TODO: Ajouter plus de tests
    print(f"✓ Tests {func_name} passés")
'''
        
        return test_code
    
    async def generate_class(
        self,
        name: str,
        purpose: str,
        attributes: List[Dict[str, str]],
        methods: List[Dict[str, Any]]
    ) -> str:
        """
        Génère une classe complète
        
        Args:
            name: Nom de la classe
            purpose: But de la classe
            attributes: Attributs {'name': '', 'type': '', 'default': ''}
            methods: Méthodes [{'name': '', 'params': [], 'purpose': ''}]
        """
        # Docstring de classe
        docstring = purpose
        if self.config.add_docstrings:
            docstring += "\n    \n    Attributes:\n"
            for attr in attributes:
                docstring += f"        {attr['name']}: {attr.get('type', 'Any')}\n"
        
        # __init__ params
        init_params = ""
        if attributes:
            init_params = ", " + ", ".join([
                f"{attr['name']}: {attr['type']}" if self.config.add_type_hints
                else attr['name']
                for attr in attributes
            ])
        
        # __init__ body
        init_body = "\n        ".join([
            f"self.{attr['name']} = {attr['name']}"
            for attr in attributes
        ])
        
        # Générer les méthodes
        methods_code = []
        for method in methods:
            method_code = await self._generate_method(method)
            methods_code.append(self._indent(method_code, 4))
        
        # Rendu
        code = self.templates['python_class'].render(
            name=name,
            docstring=docstring,
            init_params=init_params,
            init_body=init_body,
            methods="\n    ".join(methods_code)
        )
        
        self.generation_history.append({
            'type': 'class',
            'name': name,
            'code': code,
            'config': self.config.__dict__
        })
        
        return code
    
    async def _generate_method(self, method_spec: Dict[str, Any]) -> str:
        """Génère une méthode de classe"""
        name = method_spec['name']
        params = method_spec.get('params', [])
        purpose = method_spec.get('purpose', '')
        
        # Signature
        param_str = "self"
        if params:
            param_str += ", " + ", ".join([
                f"{p['name']}: {p['type']}" if self.config.add_type_hints
                else p['name']
                for p in params
            ])
        
        # Docstring
        doc = f'"""{purpose}"""' if purpose else '"""TODO: Documenter"""'
        
        # Corps
        body = method_spec.get('body', 'pass')
        
        return f'''def {name}({param_str}):
    {doc}
    {body}
'''
    
    async def generate_api_endpoint(
        self,
        route: str,
        method: str,
        name: str,
        purpose: str,
        request_model: Optional[Dict] = None,
        response_model: Optional[Dict] = None
    ) -> str:
        """Génère un endpoint API REST"""
        # Corps de l'endpoint
        body = "# TODO: Implémenter la logique\n        "
        
        if request_model:
            body += "data = request.get_json()\n        "
            body += "# Valider les données\n        "
        
        body += "result = process_request()\n        "
        
        code = self.templates['api_endpoint'].render(
            route=route,
            method=method,
            name=name,
            docstring=purpose,
            body=body
        )
        
        return code
    
    async def optimize_code(self, code: str) -> str:
        """Optimise du code existant"""
        optimizations = []
        
        # Remplacer les boucles simples par des comprehensions
        # for x in list:
        #     result.append(transform(x))
        # => result = [transform(x) for x in list]
        
        pattern = r'for (\w+) in (\w+):\s+result\.append\((.+?)\)'
        matches = re.finditer(pattern, code, re.MULTILINE)
        
        for match in matches:
            var, iterable, expr = match.groups()
            old = match.group(0)
            new = f'result = [{expr} for {var} in {iterable}]'
            code = code.replace(old, new)
            optimizations.append(f'Converti boucle en list comprehension')
        
        # Autres optimisations...
        
        return code
    
    async def add_documentation(self, code: str) -> str:
        """Ajoute de la documentation au code"""
        if not self.config.add_docstrings:
            return code
        
        # Trouver les fonctions sans docstring
        pattern = r'def (\w+)\([^)]*\):\s*\n(?!    """)'
        
        def add_doc(match):
            func_name = match.group(1)
            return match.group(0) + f'    """TODO: Documenter {func_name}"""\n'
        
        code = re.sub(pattern, add_doc, code)
        
        return code
    
    def get_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Récupère l'historique de génération"""
        return self.generation_history[-limit:]
    
    def save_code(self, code: str, filename: str):
        """Sauvegarde du code généré"""
        from pathlib import Path
        Path(filename).write_text(code, encoding='utf-8')
