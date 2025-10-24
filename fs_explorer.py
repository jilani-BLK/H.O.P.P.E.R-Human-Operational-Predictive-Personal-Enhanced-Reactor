#!/usr/bin/env python3
"""
HOPPER FileSystem Explorer - CLI de test
Permet de scanner et interroger le système de fichiers
"""

import sys
import argparse
from pathlib import Path
from loguru import logger

# Ajouter le répertoire parent au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent))

from src.filesystem.explorer import FileSystemExplorer


def format_size(size: int) -> str:
    """Formater taille en human-readable"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def cmd_scan(args):
    """Scanner un répertoire"""
    explorer = FileSystemExplorer()
    
    logger.info(f"🔍 Scan de {args.path}")
    
    stats = explorer.scan(
        Path(args.path),
        recursive=args.recursive,
        update_existing=args.update
    )
    
    print(f"\n📊 Résultats du scan:")
    print(f"  ✅ Fichiers ajoutés: {stats['files_added']}")
    print(f"  🔄 Fichiers mis à jour: {stats['files_updated']}")
    print(f"  ⏭️  Fichiers ignorés: {stats['files_skipped']}")
    
    if stats.get('errors'):
        print(f"  ⚠️  Erreurs: {len(stats['errors'])}")
        if args.verbose:
            for error in stats['errors'][:10]:
                print(f"     - {error}")
    
    print(f"\n📈 Statistiques globales:")
    print(f"  Total fichiers: {explorer.stats['total_files']}")
    print(f"  Total répertoires: {explorer.stats['total_dirs']}")
    print(f"  Taille totale: {format_size(explorer.stats['total_size'])}")


def cmd_search(args):
    """Rechercher dans l'index"""
    explorer = FileSystemExplorer()
    
    if not explorer.index:
        print("⚠️  Index vide. Lancez d'abord un scan.")
        return
    
    results = explorer.search(
        query=args.query or "",
        extension=args.extension,
        category=args.category,
        limit=args.limit
    )
    
    print(f"\n🔎 Résultats de recherche: {len(results)} fichiers")
    
    for i, metadata in enumerate(results[:args.limit], 1):
        print(f"\n{i}. {metadata.name}")
        print(f"   📁 {metadata.path}")
        print(f"   📊 {format_size(metadata.size)} | {metadata.extension}")
        if args.verbose:
            print(f"   🕐 Modifié: {metadata.modified_at}")
            print(f"   🔒 Perms: {metadata.permissions}")


def cmd_stats(args):
    """Afficher statistiques"""
    explorer = FileSystemExplorer()
    
    if not explorer.index:
        print("⚠️  Index vide. Lancez d'abord un scan.")
        return
    
    print("\n📊 Statistiques globales")
    print("=" * 50)
    print(f"Total fichiers: {explorer.stats['total_files']}")
    print(f"Total répertoires: {explorer.stats['total_dirs']}")
    print(f"Taille totale: {format_size(explorer.stats['total_size'])}")
    print(f"Dernier scan: {explorer.stats.get('last_scan', 'Jamais')}")
    
    print("\n📂 Par catégorie")
    print("=" * 50)
    
    category_stats = explorer.get_category_stats()
    for category, stats in sorted(category_stats.items(), key=lambda x: x[1]['count'], reverse=True):
        print(f"\n{category.upper()}")
        print(f"  Fichiers: {stats['count']}")
        print(f"  Taille: {format_size(stats['total_size'])}")
        print(f"  Extensions: {', '.join(sorted(stats['extensions']))}")
    
    if args.verbose:
        print("\n📏 Top 10 fichiers les plus gros")
        print("=" * 50)
        for i, metadata in enumerate(explorer.get_largest_files(10), 1):
            print(f"{i:2}. {format_size(metadata.size):>10} - {metadata.name}")
        
        print("\n🕐 Top 10 fichiers récents")
        print("=" * 50)
        from datetime import datetime
        for i, metadata in enumerate(explorer.get_recent_files(10), 1):
            modified = datetime.fromtimestamp(metadata.modified_at).strftime("%Y-%m-%d %H:%M")
            print(f"{i:2}. {modified} - {metadata.name}")


def cmd_clear(args):
    """Vider l'index"""
    explorer = FileSystemExplorer()
    
    if args.yes or input("⚠️  Confirmer la suppression de l'index ? (oui/non): ").lower() == "oui":
        explorer.clear_index()
        explorer._save_index()
        print("✅ Index vidé")
    else:
        print("❌ Annulé")


def main():
    """Point d'entrée CLI"""
    parser = argparse.ArgumentParser(
        description="🔍 HOPPER FileSystem Explorer - Scanner et explorer votre système de fichiers"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commandes disponibles")
    
    # Commande: scan
    scan_parser = subparsers.add_parser("scan", help="Scanner un répertoire")
    scan_parser.add_argument("path", help="Chemin à scanner")
    scan_parser.add_argument("-r", "--recursive", action="store_true", help="Scan récursif")
    scan_parser.add_argument("-u", "--update", action="store_true", help="Mettre à jour fichiers existants")
    scan_parser.add_argument("-v", "--verbose", action="store_true", help="Mode verbeux")
    
    # Commande: search
    search_parser = subparsers.add_parser("search", help="Rechercher dans l'index")
    search_parser.add_argument("-q", "--query", help="Recherche dans le nom")
    search_parser.add_argument("-e", "--extension", help="Filtrer par extension (.py, .js, etc.)")
    search_parser.add_argument("-c", "--category", choices=["code", "config", "docs", "data", "web", "image", "audio", "video"], help="Filtrer par catégorie")
    search_parser.add_argument("-l", "--limit", type=int, default=20, help="Nombre max de résultats")
    search_parser.add_argument("-v", "--verbose", action="store_true", help="Mode verbeux")
    
    # Commande: stats
    stats_parser = subparsers.add_parser("stats", help="Afficher statistiques")
    stats_parser.add_argument("-v", "--verbose", action="store_true", help="Stats détaillées")
    
    # Commande: clear
    clear_parser = subparsers.add_parser("clear", help="Vider l'index")
    clear_parser.add_argument("-y", "--yes", action="store_true", help="Confirmer automatiquement")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Configurer logger
    logger.remove()
    if hasattr(args, 'verbose') and args.verbose:
        logger.add(sys.stderr, level="DEBUG")
    else:
        logger.add(sys.stderr, level="INFO")
    
    # Exécuter commande
    commands = {
        "scan": cmd_scan,
        "search": cmd_search,
        "stats": cmd_stats,
        "clear": cmd_clear
    }
    
    commands[args.command](args)


if __name__ == "__main__":
    main()
