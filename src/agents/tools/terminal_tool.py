"""
Terminal Tool - Execute shell commands safely.
"""

from src.agents.tools.base_tool import BaseTool, ToolMetadata
import subprocess
import shlex
from typing import List


class TerminalTool(BaseTool):
    """
    Outil pour exécuter des commandes shell.
    
    ATTENTION : Cet outil peut être dangereux. Il devrait :
    - Requérir confirmation utilisateur
    - Avoir une whitelist de commandes autorisées
    - Être restreint pour production
    
    Usage:
        run_terminal(command="ls -la")
    """
    
    # Whitelist de commandes sûres (pour démo)
    ALLOWED_COMMANDS = {
        'ls', 'pwd', 'echo', 'cat', 'grep', 'find', 'wc',
        'head', 'tail', 'date', 'whoami', 'hostname',
        'df', 'du', 'ps', 'top'
    }
    
    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="run_terminal",
            description="Execute a safe shell command and return output",
            schema={
                "parameters": {
                    "command": {
                        "type": "string",
                        "description": "Shell command to execute",
                        "required": True
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Timeout in seconds (default: 10)",
                        "required": False
                    }
                }
            },
            category="system",
            requires_confirmation=True
        )
    
    def _is_command_safe(self, command: str) -> tuple[bool, str]:
        """
        Vérifie si une commande est sûre.
        
        Returns:
            (is_safe, reason)
        """
        # Interdire certains caractères dangereux
        dangerous_chars = [';', '|', '&', '>', '<', '`', '$', '(', ')']
        for char in dangerous_chars:
            if char in command:
                return False, f"Dangerous character '{char}' not allowed"
        
        # Extraire la commande principale
        parts = shlex.split(command)
        if not parts:
            return False, "Empty command"
        
        main_command = parts[0]
        
        # Vérifier whitelist
        if main_command not in self.ALLOWED_COMMANDS:
            return False, f"Command '{main_command}' not in whitelist"
        
        return True, ""
    
    async def execute(self, command: str, timeout: int = 10) -> str:
        """
        Exécute une commande shell.
        
        Args:
            command: Commande à exécuter
            timeout: Timeout en secondes
            
        Returns:
            Output de la commande ou erreur
        """
        # Validation sécurité
        is_safe, reason = self._is_command_safe(command)
        if not is_safe:
            return f"❌ Command rejected: {reason}"
        
        try:
            # SÉCURITÉ: Utiliser shell=False pour éviter injection
            # Convertir string en liste de commandes
            parts = shlex.split(command)
            
            # Exécuter commande (PAS de shell)
            result = subprocess.run(
                parts,  # Liste, pas string
                shell=False,  # ✅ SÉCURISÉ - pas de shell
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd="/tmp"  # Toujours exécuter depuis /tmp pour sécurité
            )
            
            # Formater output
            output = result.stdout.strip()
            error = result.stderr.strip()
            
            if result.returncode != 0:
                return f"❌ Command failed (code {result.returncode}):\n{error}"
            
            # Limiter la taille de l'output
            if len(output) > 1000:
                output = output[:1000] + "\n... (output truncated)"
            
            return f"✅ Command executed successfully:\n{output}"
        
        except subprocess.TimeoutExpired:
            return f"❌ Command timed out after {timeout} seconds"
        except Exception as e:
            return f"❌ Error executing command: {str(e)}"


class GetSystemInfoTool(BaseTool):
    """
    Outil pour obtenir des informations système.
    
    Usage:
        get_system_info()
    """
    
    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="get_system_info",
            description="Get system information (OS, hostname, current directory, etc.)",
            schema={
                "parameters": {}
            },
            category="system",
            requires_confirmation=False
        )
    
    async def execute(self) -> str:
        """
        Récupère les informations système.
        
        Returns:
            Informations système formatées
        """
        try:
            # Hostname
            hostname_result = subprocess.run(
                ["hostname"], capture_output=True, text=True, timeout=5
            )
            hostname = hostname_result.stdout.strip()
            
            # Current user
            whoami_result = subprocess.run(
                ["whoami"], capture_output=True, text=True, timeout=5
            )
            whoami = whoami_result.stdout.strip()
            
            # Current directory
            pwd_result = subprocess.run(
                ["pwd"], capture_output=True, text=True, timeout=5
            )
            pwd = pwd_result.stdout.strip()
            
            # Date
            date_result = subprocess.run(
                ["date"], capture_output=True, text=True, timeout=5
            )
            date = date_result.stdout.strip()
            
            output = f"""✅ System Information:
  Hostname: {hostname}
  User: {whoami}
  Current Dir: {pwd}
  Date: {date}
"""
            return output
        
        except Exception as e:
            return f"❌ Error getting system info: {str(e)}"


# Tests
async def test_terminal_tools():
    """Test des outils terminal."""
    print("="*60)
    print("Testing Terminal Tools")
    print("="*60)
    
    terminal_tool = TerminalTool()
    sysinfo_tool = GetSystemInfoTool()
    
    # Test 1: System info
    print("\n💻 Test 1: System info")
    result = await sysinfo_tool.execute()
    print(f"  {result}")
    
    # Test 2: Safe command (ls)
    print("\n✅ Test 2: Safe command (ls)")
    result = await terminal_tool.execute(command="ls -la")
    print(f"  {result[:200]}...")  # Truncate
    
    # Test 3: Safe command (echo)
    print("\n✅ Test 3: Safe command (echo)")
    result = await terminal_tool.execute(command='echo "Hello from HOPPER"')
    print(f"  {result}")
    
    # Test 4: Safe command (pwd)
    print("\n✅ Test 4: Safe command (pwd)")
    result = await terminal_tool.execute(command="pwd")
    print(f"  {result}")
    
    # Test 5: Dangerous command (rejected)
    print("\n❌ Test 5: Dangerous command (should be rejected)")
    result = await terminal_tool.execute(command="rm -rf /")
    print(f"  {result}")
    
    # Test 6: Pipe character (rejected)
    print("\n❌ Test 6: Pipe character (should be rejected)")
    result = await terminal_tool.execute(command="ls | grep test")
    print(f"  {result}")
    
    # Test 7: Timeout
    print("\n⏱️  Test 7: Timeout (2 seconds)")
    result = await terminal_tool.execute(command="sleep 20", timeout=2)
    print(f"  {result}")
    
    print("\n" + "="*60)
    print("✅ Terminal tools tests completed!")
    print("="*60)


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_terminal_tools())
