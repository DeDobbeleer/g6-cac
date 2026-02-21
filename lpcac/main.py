"""CLI principal - PoC Pipeline de données."""
import typer
from pathlib import Path
from typing import Optional
import yaml
from rich.console import Console
from rich.table import Table
from rich import box

from lpcac.models import Repo, RoutingPolicy, NormalizationPolicy, ProcessingPolicy
from lpcac.connectors import DirectorConnector

app = typer.Typer(help="Logpoint CaC - Pipeline de données")
console = Console()


# ============================================================
# COMMANDES
# ============================================================

@app.command()
def validate(
    config_path: Path = typer.Argument(..., help="Chemin vers le fichier ou dossier YAML"),
):
    """Valide la syntaxe et les schémas des fichiers de configuration."""
    files = _find_yaml_files(config_path)
    
    table = Table(title="Validation des configurations", box=box.ROUNDED)
    table.add_column("Fichier", style="cyan")
    table.add_column("Type", style="magenta")
    table.add_column("Statut", style="green")
    table.add_column("Message", style="yellow")
    
    errors = 0
    for file in files:
        try:
            with open(file) as f:
                data = yaml.safe_load(f)
            
            if not data or "kind" not in data:
                table.add_row(str(file), "?", "[red]SKIP[/red]", "Pas de champ 'kind'")
                continue
            
            kind = data.get("kind")
            result = _validate_resource(kind, data.get("spec", {}))
            
            if result["valid"]:
                table.add_row(str(file), kind, "[green]OK[/green]", "-")
            else:
                table.add_row(str(file), kind, "[red]ERROR[/red]", result["error"])
                errors += 1
                
        except yaml.YAMLError as e:
            table.add_row(str(file), "?", "[red]YAML ERR[/red]", str(e))
            errors += 1
        except Exception as e:
            table.add_row(str(file), "?", "[red]ERROR[/red]", str(e))
            errors += 1
    
    console.print(table)
    
    if errors > 0:
        raise typer.Exit(code=1)


@app.command()
def plan(
    config_path: Path = typer.Argument(..., help="Chemin vers le dossier de configs"),
    pool: str = typer.Option(..., help="UUID du pool Director"),
    logpoint: str = typer.Option(..., help="ID du logpoint"),
    director_url: str = typer.Option(..., envvar="DIRECTOR_URL", help="URL Director"),
    token: str = typer.Option(..., envvar="DIRECTOR_TOKEN", help="Token API"),
):
    """Compare la config déclarée avec l'état réel (dry-run)."""
    console.print("[bold blue]Analyse des différences...[/bold blue]")
    
    # Charger les configs locales
    declared = _load_all_configs(config_path)
    console.print(f"Configs locales trouvées : {len(declared)} ressources")
    
    # Récupérer l'état réel
    try:
        with DirectorConnector(director_url, token, pool) as conn:
            actual_repos = conn.list_repos(logpoint)
            console.print(f"Repos existants : {len(actual_repos)}")
            
            # TODO: Comparer et afficher le diff
            table = Table(title="Diff Déclaré vs Réel", box=box.ROUNDED)
            table.add_column("Ressource", style="cyan")
            table.add_column("Action", style="magenta")
            table.add_column("Détails", style="yellow")
            
            for name, config in declared.items():
                action = _determine_action(name, config, actual_repos)
                table.add_row(name, action["type"], action["detail"])
            
            console.print(table)
            
    except Exception as e:
        console.print(f"[red]Erreur connexion Director: {e}[/red]")
        raise typer.Exit(code=1)


# ============================================================
# UTILS
# ============================================================

def _find_yaml_files(path: Path) -> list[Path]:
    """Trouve tous les fichiers YAML dans un chemin."""
    if path.is_file():
        return [path]
    return list(path.rglob("*.yaml")) + list(path.rglob("*.yml"))


def _validate_resource(kind: str, spec: dict) -> dict:
    """Valide une ressource selon son type."""
    try:
        if kind == "Repo":
            Repo(**spec)
        elif kind == "RoutingPolicy":
            RoutingPolicy(**spec)
        elif kind == "NormalizationPolicy":
            NormalizationPolicy(**spec)
        elif kind == "ProcessingPolicy":
            ProcessingPolicy(**spec)
        else:
            return {"valid": False, "error": f"Type inconnu: {kind}"}
        return {"valid": True}
    except Exception as e:
        return {"valid": False, "error": str(e)}


def _load_all_configs(path: Path) -> dict:
    """Charge toutes les configs YAML d'un dossier."""
    configs = {}
    for file in _find_yaml_files(path):
        try:
            with open(file) as f:
                data = yaml.safe_load(f)
            if data and "spec" in data and "name" in data.get("spec", {}):
                configs[data["spec"]["name"]] = data
        except:
            continue
    return configs


def _determine_action(name: str, config: dict, actual: list) -> dict:
    """Détermine l'action nécessaire (create/update/delete)."""
    actual_names = {r.get("name", r.get("repo_name", "")) for r in actual}
    
    if name not in actual_names:
        return {"type": "[green]CREATE[/green]", "detail": "Nouvelle ressource"}
    
    # TODO: Comparer les champs pour détecter UPDATE
    return {"type": "[yellow]UNCHANGED[/yellow]", "detail": "Existe déjà"}


if __name__ == "__main__":
    app()
