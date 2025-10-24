#!/usr/bin/env python3
"""
HOPPER Terminal User Interface (TUI)
Interface interactive élégante dans le terminal
"""

from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, Horizontal, ScrollableContainer
from textual.widgets import (
    Header, Footer, Static, Input, Button, 
    Label, RichLog, ProgressBar, DataTable
)
from textual.reactive import reactive
from rich.text import Text
from rich.panel import Panel
from rich.table import Table as RichTable
from datetime import datetime
import asyncio
import aiohttp
from aiohttp import ClientTimeout
from typing import Optional
import sys
import os

# Ajouter le chemin pour les imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'orchestrator'))


class StatusPanel(Static):
    """Panneau d'état système"""
    
    status = reactive("🟢 En ligne")
    modules_count = reactive(0)
    last_update = reactive("")
    
    def render(self) -> Panel:
        content = Text()
        content.append("🧠 HOPPER Status\n\n", style="bold cyan")
        content.append(f"État: {self.status}\n", style="bold")
        content.append(f"Modules: {self.modules_count}\n")
        content.append(f"Dernière mise à jour: {self.last_update}\n", style="dim")
        
        return Panel(
            content,
            title="[bold cyan]Système[/bold cyan]",
            border_style="cyan"
        )


class ModulesPanel(Static):
    """Panneau des modules actifs"""
    
    modules = reactive([])
    
    def render(self) -> Panel:
        if not self.modules:
            content = Text("Chargement des modules...", style="dim italic")
        else:
            table = RichTable(show_header=True, header_style="bold magenta")
            table.add_column("Module", style="cyan")
            table.add_column("Type", style="yellow")
            table.add_column("État", style="green")
            
            for module in self.modules:
                table.add_row(
                    module.get("name", "Unknown"),
                    module.get("type", "N/A"),
                    "✅ Actif" if module.get("active") else "❌ Inactif"
                )
            
            content = table
        
        return Panel(
            content,
            title="[bold magenta]Modules Coordonnés[/bold magenta]",
            border_style="magenta"
        )


class ConversationLog(RichLog):
    """Journal de conversation"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.can_focus = False
        
    def add_message(self, role: str, content: str):
        """Ajouter un message au journal"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if role == "user":
            style = "bold cyan"
            icon = "👤"
        elif role == "hopper":
            style = "bold green"
            icon = "🤖"
        else:
            style = "dim"
            icon = "ℹ️"
        
        self.write(f"[dim]{timestamp}[/dim] {icon} [{style}]{role.upper()}[/{style}]: {content}")


class HopperTUI(App):
    """Application TUI principale pour HOPPER"""
    
    CSS = """
    Screen {
        background: $surface;
    }
    
    #main-container {
        height: 100%;
        layout: grid;
        grid-size: 2 2;
        grid-rows: 1fr 3fr;
        grid-columns: 2fr 1fr;
    }
    
    #status-panel {
        row-span: 1;
        column-span: 1;
    }
    
    #modules-panel {
        row-span: 1;
        column-span: 1;
    }
    
    #conversation-container {
        row-span: 1;
        column-span: 2;
        height: 100%;
    }
    
    #conversation-log {
        height: 1fr;
        border: solid $primary;
        background: $surface;
        padding: 1;
    }
    
    #input-container {
        height: auto;
        dock: bottom;
        background: $surface;
        padding: 1;
    }
    
    #input-field {
        width: 1fr;
    }
    
    #send-button {
        width: auto;
        margin-left: 1;
    }
    
    Button {
        margin: 0 1;
    }
    
    Input {
        border: solid $primary;
    }
    
    .panel {
        border: solid $primary;
        padding: 1;
    }
    """
    
    BINDINGS = [
        ("q", "quit", "Quitter"),
        ("ctrl+c", "quit", "Quitter"),
        ("ctrl+l", "clear_log", "Effacer"),
        ("ctrl+r", "refresh", "Actualiser"),
    ]
    
    def __init__(self, orchestrator_url: str = "http://localhost:5050"):
        super().__init__()
        self.orchestrator_url = orchestrator_url
        self.session: Optional[aiohttp.ClientSession] = None
        
    def compose(self) -> ComposeResult:
        """Créer l'interface"""
        yield Header(show_clock=True)
        
        with Container(id="main-container"):
            yield StatusPanel(id="status-panel")
            yield ModulesPanel(id="modules-panel")
            
            with Vertical(id="conversation-container"):
                yield ConversationLog(id="conversation-log", highlight=True, markup=True)
                
                with Horizontal(id="input-container"):
                    yield Input(
                        placeholder="Parlez à HOPPER...",
                        id="input-field"
                    )
                    yield Button("Envoyer", variant="primary", id="send-button")
        
        yield Footer()
    
    async def on_mount(self) -> None:
        """Au démarrage de l'app"""
        self.title = "🧠 HOPPER - Assistant Personnel Intelligent"
        self.sub_title = f"Connecté à {self.orchestrator_url}"
        
        # Initialiser la session HTTP
        self.session = aiohttp.ClientSession()
        
        # Message de bienvenue
        log = self.query_one("#conversation-log", ConversationLog)
        log.write("[bold cyan]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold cyan]")
        log.write("[bold green]🧠 HOPPER - Human Operational Predictive Personal Enhanced Reactor[/bold green]")
        log.write("[bold cyan]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold cyan]")
        log.write("")
        log.write("[dim]Bienvenue ! Je suis HOPPER, votre assistant personnel intelligent.[/dim]")
        log.write("[dim]Tous mes modules sont coordonnés et reliés au noyau. Prêt à vous servir ![/dim]")
        log.write("")
        
        # Démarrer la mise à jour du statut
        self.set_interval(3.0, self.update_status)
        await self.update_status()
        
        # Focus sur l'input
        self.query_one("#input-field", Input).focus()
    
    async def on_unmount(self) -> None:
        """Au démontage de l'app"""
        if self.session:
            await self.session.close()
    
    async def update_status(self) -> None:
        """Mettre à jour le statut système"""
        try:
            if not self.session:
                return
                
            # Récupérer le statut
            async with self.session.get(f"{self.orchestrator_url}/health", timeout=ClientTimeout(total=2)) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Mettre à jour le panneau de statut
                    status_panel = self.query_one("#status-panel", StatusPanel)
                    status_panel.status = "🟢 En ligne"
                    status_panel.last_update = datetime.now().strftime("%H:%M:%S")
                    
                    # Récupérer les statistiques du hub si disponible
                    try:
                        async with self.session.get(
                            f"{self.orchestrator_url}/coordination/stats", 
                            timeout=ClientTimeout(total=2)
                        ) as stats_response:
                            if stats_response.status == 200:
                                stats_data = await stats_response.json()
                                status_panel.modules_count = stats_data.get("total_modules", 0)
                                
                                # Mettre à jour les modules
                                modules_panel = self.query_one("#modules-panel", ModulesPanel)
                                modules = []
                                for module_name, module_type in stats_data.get("modules_by_type", {}).items():
                                    modules.append({
                                        "name": module_name,
                                        "type": module_type,
                                        "active": True
                                    })
                                modules_panel.modules = modules[:10]  # Limiter à 10 pour l'affichage
                    except:
                        pass
                else:
                    status_panel = self.query_one("#status-panel", StatusPanel)
                    status_panel.status = "🟡 Limité"
                    
        except Exception as e:
            status_panel = self.query_one("#status-panel", StatusPanel)
            status_panel.status = f"🔴 Hors ligne"
            status_panel.last_update = datetime.now().strftime("%H:%M:%S")
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Gérer les clics sur les boutons"""
        if event.button.id == "send-button":
            await self.send_message()
    
    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Gérer la soumission de l'input (Enter)"""
        await self.send_message()
    
    async def send_message(self) -> None:
        """Envoyer un message à HOPPER"""
        input_field = self.query_one("#input-field", Input)
        message = input_field.value.strip()
        
        if not message:
            return
        
        # Effacer l'input
        input_field.value = ""
        
        # Ajouter le message utilisateur au log
        log = self.query_one("#conversation-log", ConversationLog)
        log.add_message("user", message)
        
        try:
            if not self.session:
                log.add_message("system", "❌ Session HTTP non initialisée")
                return
            
            # Envoyer à l'orchestrateur
            log.write("[dim]⏳ Traitement en cours...[/dim]")
            
            async with self.session.post(
                f"{self.orchestrator_url}/process",
                json={"query": message},
                timeout=ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    response_text = data.get("response", "Pas de réponse")
                    log.add_message("hopper", response_text)
                else:
                    error_text = await response.text()
                    log.add_message("system", f"❌ Erreur {response.status}: {error_text}")
                    
        except asyncio.TimeoutError:
            log.add_message("system", "⏱️ Timeout - La requête a pris trop de temps")
        except Exception as e:
            log.add_message("system", f"❌ Erreur: {str(e)}")
    
    def action_clear_log(self) -> None:
        """Effacer le journal"""
        log = self.query_one("#conversation-log", ConversationLog)
        log.clear()
        log.write("[dim]Journal effacé[/dim]")
    
    async def action_refresh(self) -> None:
        """Actualiser le statut"""
        await self.update_status()
        log = self.query_one("#conversation-log", ConversationLog)
        log.write("[dim]🔄 Statut actualisé[/dim]")
    
    def action_quit(self) -> None:
        """Quitter l'application"""
        self.exit()


def main():
    """Point d'entrée principal"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="🧠 HOPPER TUI - Interface Terminal Interactive"
    )
    parser.add_argument(
        "--url",
        default="http://localhost:5050",
        help="URL de l'orchestrateur HOPPER (défaut: http://localhost:5050)"
    )
    
    args = parser.parse_args()
    
    app = HopperTUI(orchestrator_url=args.url)
    app.run()


if __name__ == "__main__":
    main()
