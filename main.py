"""
NetAudit - Outil d'audit de conformité réseau
IMT Nord Europe | Mode simulation (Dry Run) activé
"""

import yaml
import os
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich import box

console = Console()

# =============================================================================
# RÈGLES DE SÉCURITÉ À VÉRIFIER
# Facile d'en ajouter sans toucher au cœur du programme !
# =============================================================================
REGLES_SECURITE = {
    "Serveur HTTP désactivé":       ("no ip http server",          "CRITIQUE"),
    "Serveur HTTPS désactivé":      ("no ip http secure-server",   "CRITIQUE"),
    "Telnet interdit (VTY SSH)":    ("transport input ssh",        "CRITIQUE"),
    "Timeout de session défini":    ("exec-timeout",               "MOYEN"),
    "Banner de connexion présente": ("banner motd",                "FAIBLE"),
}

# =============================================================================
# SIMULATION : configs fictives qui remplacent un vrai "show run"
# =============================================================================
CONFIGS_SIMULEES = {
    "192.168.1.1": """
        hostname RouterParis
        no ip http server
        no ip http secure-server
        banner motd # Acces restreint au personnel autorise #
        line vty 0 4
         transport input ssh
         exec-timeout 5 0
    """,
    "192.168.1.2": """
        hostname RouterLyon
        ip http server
        no ip http secure-server
        line vty 0 4
         transport input telnet ssh
    """,
    "192.168.1.3": """
        hostname RouterLille
        ip http server
        ip http secure-server
        line vty 0 4
         transport input all
    """,
}

# =============================================================================
# INVENTAIRE DES ÉQUIPEMENTS
# En production : lu depuis inventory.yaml
# =============================================================================
INVENTAIRE = [
    {"host": "192.168.1.1", "name": "Router-Paris",  "site": "Paris"},
    {"host": "192.168.1.2", "name": "Router-Lyon",   "site": "Lyon"},
    {"host": "192.168.1.3", "name": "Router-Lille",  "site": "Lille"},
]


def get_config(device: dict, dry_run: bool) -> str | None:
    """Récupère la config du routeur (SSH réel ou simulation)."""
    if dry_run:
        console.print(f"  [dim]↳ Mode simulation — chargement config fictive[/dim]")
        return CONFIGS_SIMULEES.get(device["host"], "")
    else:
        try:
            from netmiko import ConnectHandler
            params = {
                "device_type": "cisco_ios",
                "host":        device["host"],
                "username":    device.get("username", "admin"),
                "password":    device.get("password", ""),
            }
            conn = ConnectHandler(**params)
            config = conn.send_command("show running-config")
            conn.disconnect()
            return config
        except Exception as e:
            console.print(f"  [red]↳ Erreur SSH : {e}[/red]")
            return None


def analyser_config(config: str) -> list[dict]:
    """Vérifie chaque règle de sécurité dans la config."""
    resultats = []
    for nom_regle, (pattern, criticite) in REGLES_SECURITE.items():
        conforme = pattern in config
        resultats.append({
            "regle":      nom_regle,
            "criticite":  criticite,
            "conforme":   conforme,
        })
    return resultats


def afficher_rapport(resultats_globaux: list[dict]):
    """Affiche le tableau de synthèse final."""
    table = Table(
        title=f"\n🛡️  Rapport de Conformité — NetAudit\n"
              f"[dim]Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}[/dim]",
        box=box.ROUNDED,
        show_lines=True,
    )
    table.add_column("Équipement",    style="cyan",    min_width=18)
    table.add_column("Site",          style="blue",    min_width=8)
    table.add_column("Règle vérifiée",style="magenta", min_width=28)
    table.add_column("Criticité",     justify="center",min_width=10)
    table.add_column("Statut",        justify="center",min_width=12)

    total, conformes = 0, 0

    for entree in resultats_globaux:
        for r in entree["resultats"]:
            criticite_style = {
                "CRITIQUE": "[bold red]CRITIQUE[/bold red]",
                "MOYEN":    "[yellow]MOYEN[/yellow]",
                "FAIBLE":   "[green]FAIBLE[/green]",
            }.get(r["criticite"], r["criticite"])

            statut = "✅ OK" if r["conforme"] else "❌ VULNÉRABLE"
            statut_style = f"[green]{statut}[/green]" if r["conforme"] else f"[bold red]{statut}[/bold red]"

            table.add_row(
                entree["name"],
                entree["site"],
                r["regle"],
                criticite_style,
                statut_style,
            )
            total += 1
            if r["conforme"]:
                conformes += 1

    console.print(table)

    # Score global
    score = int((conformes / total) * 100) if total > 0 else 0
    couleur = "green" if score >= 80 else ("yellow" if score >= 50 else "red")
    console.print(
        f"\n[bold]Score global de conformité : [{couleur}]{score}%[/{couleur}]"
        f"[/bold] ({conformes}/{total} règles respectées)\n"
    )


def lancer_audit(dry_run: bool = True):
    console.print("\n[bold cyan]═══════════════════════════════════════[/bold cyan]")
    console.print("[bold cyan]   🔍 NetAudit — Démarrage de l'audit   [/bold cyan]")
    console.print(f"[bold cyan]═══════════════════════════════════════[/bold cyan]")
    console.print(f"[dim]Mode : {'⚙️  Simulation (Dry Run)' if dry_run else '🌐 SSH Réel'}[/dim]\n")

    resultats_globaux = []

    for device in INVENTAIRE:
        console.print(f"[yellow]▶ Audit de {device['name']} ({device['host']})[/yellow]")
        config = get_config(device, dry_run)

        if config is None:
            console.print(f"  [red]↳ Impossible de récupérer la config — équipement ignoré[/red]")
            continue

        resultats = analyser_config(config)
        resultats_globaux.append({
            "name":      device["name"],
            "site":      device["site"],
            "host":      device["host"],
            "resultats": resultats,
        })
        console.print(f"  [green]↳ Analyse terminée ({len(resultats)} règles vérifiées)[/green]")

    afficher_rapport(resultats_globaux)


if __name__ == "__main__":
    # dry_run=True  → simulation pure, pas de réseau nécessaire
    # dry_run=False → connexion SSH réelle (nécessite netmiko + routeur dispo)
    lancer_audit(dry_run=True)
