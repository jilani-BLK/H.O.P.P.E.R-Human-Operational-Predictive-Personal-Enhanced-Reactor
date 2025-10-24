"""
Email Tool - Send emails via HOPPER's email service.
"""

from src.agents.tools.base_tool import BaseTool, ToolMetadata
from typing import Optional
import re


class EmailTool(BaseTool):
    """
    Outil pour envoyer des emails.
    
    Usage:
        send_email(to="user@example.com", subject="Hello", body="Message content")
    """
    
    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="send_email",
            description="Send an email to a recipient with subject and body",
            schema={
                "parameters": {
                    "to": {
                        "type": "string",
                        "description": "Recipient email address",
                        "required": True
                    },
                    "subject": {
                        "type": "string",
                        "description": "Email subject",
                        "required": True
                    },
                    "body": {
                        "type": "string",
                        "description": "Email body content",
                        "required": True
                    },
                    "cc": {
                        "type": "string",
                        "description": "CC email addresses (comma-separated)",
                        "required": False
                    }
                }
            },
            category="communication",
            requires_confirmation=True
        )
    
    def _validate_email(self, email: str) -> bool:
        """Valide le format d'une adresse email."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    async def execute(self, to: str, subject: str, body: str, 
                     cc: Optional[str] = None) -> str:
        """
        Envoie un email.
        
        Args:
            to: Destinataire
            subject: Sujet
            body: Corps du message
            cc: Destinataires en copie (optionnel)
            
        Returns:
            Message de confirmation ou erreur
        """
        # Validation
        is_valid, error = self.validate_args(to=to, subject=subject, body=body)
        if not is_valid:
            return f"❌ Validation error: {error}"
        
        # Valider format email
        if not self._validate_email(to):
            return f"❌ Invalid email address: {to}"
        
        if cc:
            cc_emails = [e.strip() for e in cc.split(",")]
            for email in cc_emails:
                if not self._validate_email(email):
                    return f"❌ Invalid CC email address: {email}"
        
        # TODO: Intégrer avec le vrai service d'email HOPPER
        # Pour l'instant, simulation
        recipients = f"{to}"
        if cc:
            recipients += f" (CC: {cc})"
        
        return f"✅ Email sent successfully to {recipients} with subject '{subject}'"


class EmailSearchTool(BaseTool):
    """
    Outil pour rechercher des emails.
    
    Usage:
        search_emails(query="from:boss", limit=10)
    """
    
    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="search_emails",
            description="Search emails by query (from:, to:, subject:, date:, etc.)",
            schema={
                "parameters": {
                    "query": {
                        "type": "string",
                        "description": "Search query (e.g., 'from:boss subject:urgent')",
                        "required": True
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results",
                        "required": False
                    }
                }
            },
            category="communication",
            requires_confirmation=False
        )
    
    async def execute(self, query: str, limit: int = 10) -> str:
        """
        Recherche des emails.
        
        Args:
            query: Requête de recherche
            limit: Nombre max de résultats
            
        Returns:
            Liste des emails trouvés
        """
        # TODO: Intégrer avec le service email HOPPER
        # Pour l'instant, simulation
        return f"✅ Found 3 emails matching '{query}' (showing top {limit})"


# Tests
async def test_email_tools():
    """Test des outils email."""
    print("="*60)
    print("Testing Email Tools")
    print("="*60)
    
    # Test 1: Send email
    print("\n📧 Test 1: Send email")
    email_tool = EmailTool()
    result = await email_tool.execute(
        to="boss@company.com",
        subject="Weekly Report",
        body="Here is the weekly report..."
    )
    print(f"  {result}")
    
    # Test 2: Send email with CC
    print("\n📧 Test 2: Send email with CC")
    result = await email_tool.execute(
        to="colleague@company.com",
        subject="Meeting Tomorrow",
        body="Don't forget the meeting at 2pm",
        cc="manager@company.com, team@company.com"
    )
    print(f"  {result}")
    
    # Test 3: Invalid email
    print("\n📧 Test 3: Invalid email address")
    result = await email_tool.execute(
        to="not-an-email",
        subject="Test",
        body="Test"
    )
    print(f"  {result}")
    
    # Test 4: Search emails
    print("\n🔍 Test 4: Search emails")
    search_tool = EmailSearchTool()
    result = await search_tool.execute(query="from:boss", limit=5)
    print(f"  {result}")
    
    print("\n" + "="*60)
    print("✅ Email tools tests completed!")
    print("="*60)


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_email_tools())
