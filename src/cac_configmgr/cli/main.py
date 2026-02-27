"""CLI entry point for CaC-ConfigMgr."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich import box

from ..utils import load_yaml, load_instance, load_fleet, load_multi_file_template, YamlError
from ..core import ResolutionEngine, filter_internal_ids, ConsistencyValidator

app = typer.Typer(help="Configuration as Code Manager for LogPoint")
console = Console()


@app.command()
def validate(
    config_path: Path = typer.Argument(..., help="Path to config file or directory"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
):
    """Validate configuration syntax and consistency."""
    console.print(f"[bold blue]Validating {config_path}...[/bold blue]\n")
    
    files = _find_config_files(config_path)
    if not files:
        console.print("[red]No configuration files found.[/red]")
        raise typer.Exit(code=1)
    
    table = Table(title="Validation Results", box=box.ROUNDED)
    table.add_column("File", style="cyan")
    table.add_column("Type", style="magenta")
    table.add_column("Status", style="green")
    table.add_column("Details", style="yellow")
    
    errors = 0
    warnings = 0
    
    for file in files:
        try:
            data = load_yaml(file)
            kind = data.get("kind", "Unknown")
            
            # Try to validate based on kind
            if kind == "Fleet":
                load_fleet(file)
                table.add_row(str(file), "Fleet", "[green]✓ OK[/green]", "-")
            elif kind == "ConfigTemplate":
                load_multi_file_template(file.parent if file.parent.name else file)
                table.add_row(str(file), "Template", "[green]✓ OK[/green]", "-")
            elif kind == "TopologyInstance":
                load_instance(file)
                table.add_row(str(file), "Instance", "[green]✓ OK[/green]", "-")
            else:
                table.add_row(str(file), kind, "[yellow]⚠ Unknown[/yellow]", f"Kind: {kind}")
                warnings += 1
                
        except YamlError as e:
            table.add_row(str(file), "?", "[red]✗ ERROR[/red]", str(e))
            errors += 1
        except Exception as e:
            table.add_row(str(file), "?", "[red]✗ ERROR[/red]", str(e))
            errors += 1
    
    console.print(table)
    console.print()
    
    # Summary
    total = len(files)
    success = total - errors - warnings
    console.print(f"[bold]Summary:[/bold] {success} OK, {warnings} warnings, {errors} errors")
    
    if errors > 0:
        raise typer.Exit(code=1)
    elif warnings > 0:
        console.print("[yellow]Validation passed with warnings.[/yellow]")
    else:
        console.print("[green]✓ All configurations valid![/green]")


@app.command()
def plan(
    fleet: Path = typer.Option(..., "--fleet", "-f", help="Path to fleet.yaml"),
    topology: Path = typer.Option(..., "--topology", "-t", help="Path to instance.yaml"),
    templates_dir: Path = typer.Option(
        "./templates", "--templates-dir", help="Templates directory"
    ),
    output: str = typer.Option("text", "--output", "-o", help="Output format: text, json"),
):
    """Preview changes (dry-run) - compare desired vs actual state."""
    console.print("[bold blue]Planning changes...[/bold blue]\n")
    
    try:
        # Load configuration
        instance = load_instance(topology)
        fleet_config = load_fleet(fleet)
        
        console.print(f"[cyan]Instance:[/cyan] {instance.metadata.name}")
        console.print(f"[cyan]Fleet:[/cyan] {fleet_config.metadata.name}")
        console.print(f"[cyan]Extends:[/cyan] {instance.metadata.extends}")
        console.print()
        
        # Resolve template chain
        engine = ResolutionEngine(templates_dir)
        resolved = engine.resolve(instance)
        
        # Display resolved configuration
        table = Table(title="Resolved Configuration", box=box.ROUNDED)
        table.add_column("Resource Type", style="cyan")
        table.add_column("Count", style="magenta")
        table.add_column("Names", style="green")
        
        for resource_type, resources in resolved.resources.items():
            if resources:
                count = len(resources)
                names = ", ".join(
                    r.get("name", r.get("policy_name", r.get("_id", "unnamed")))
                    for r in resources[:3]
                )
                if len(resources) > 3:
                    names += f" (+{len(resources) - 3} more)"
                table.add_row(resource_type, str(count), names)
        
        console.print(table)
        console.print()
        
        # Show variables
        if resolved.variables:
            var_table = Table(title="Variables", box=box.ROUNDED)
            var_table.add_column("Name", style="cyan")
            var_table.add_column("Value", style="green")
            for name, value in resolved.variables.items():
                var_table.add_row(name, str(value))
            console.print(var_table)
            console.print()
        
        # Validate resource consistency
        validator = ConsistencyValidator(resolved.resources)
        consistency_errors = validator.validate()
        
        if consistency_errors:
            console.print("[bold red]Consistency Errors:[/bold red]")
            for error in consistency_errors:
                console.print(f"  [red]•[/red] {error.resource_type}.{error.resource_name}.{error.field}: {error.message}")
            console.print()
            console.print("[yellow]⚠ Configuration has consistency issues. Review before applying.[/yellow]")
            console.print()
        else:
            console.print("[green]✓ All resource references are consistent[/green]")
            console.print()
        
        # Show template chain
        chain_table = Table(title="Template Chain (Root → Leaf)", box=box.ROUNDED)
        chain_table.add_column("Level", style="cyan")
        chain_table.add_column("Template", style="magenta")
        chain_table.add_column("Type", style="green")
        
        for i, template in enumerate(resolved.source_chain.templates):
            level = i + 1
            name = template.metadata.name
            template_type = "Instance" if isinstance(template, type(instance)) else "Template"
            chain_table.add_row(str(level), name, template_type)
        
        console.print(chain_table)
        console.print()
        
        console.print("[green]✓ Plan complete. No changes applied (dry-run).[/green]")
        console.print("[dim]Use 'apply' command to deploy these changes.[/dim]")
        
    except Exception as e:
        console.print(f"[red]Error during planning: {e}[/red]")
        raise typer.Exit(code=1)


@app.command()
def generate_demo(
    output_dir: Path = typer.Option(
        "./demo-configs", "--output", "-o", help="Output directory"
    ),
):
    """Generate demo configurations for presentation."""
    console.print("[bold blue]Generating demo configurations...[/bold blue]\n")
    
    from ..demo_generator import generate_all_configs
    
    try:
        generate_all_configs(output_dir)
        console.print(f"[green]✓ Demo configs generated in: {output_dir}[/green]")
        console.print()
        console.print("[bold]Structure:[/bold]")
        console.print("  templates/logpoint/         # Golden Templates (Level 1)")
        console.print("    ├── golden-base/          # Standard baseline")
        console.print("    ├── golden-pci-dss/       # PCI compliance addon")
        console.print("    └── golden-iso27001/      # ISO addon")
        console.print()
        console.print("  templates/mssp/acme-corp/   # MSSP Templates (Level 2-3)")
        console.print("    ├── base/                 # MSSP base (extends golden)")
        console.print("    ├── addons/")
        console.print("    │   ├── banking/          # Banking addon (horizontal)")
        console.print("    │   └── healthcare/       # Healthcare addon (horizontal)")
        console.print("    └── profiles/")
        console.print("        ├── simple/           # Simple profile")
        console.print("        ├── enterprise/       # Enterprise profile")
        console.print("        └── banking-premium/  # Banking profile (extends enterprise)")
        console.print()
        console.print("  instances/                  # Client Instances (Level 4)")
        console.print("    ├── banks/")
        console.print("    │   ├── bank-a/")
        console.print("    │   │   ├── prod/")
        console.print("    │   │   └── staging/")
        console.print("    │   └── bank-b/")
        console.print("    │       └── prod/")
        console.print("    └── enterprises/")
        console.print("        └── corp-x/")
        console.print("            └── prod/")
        console.print()
        console.print("[dim]Validate: cac-configmgr validate {output_dir}[/dim]")
        
    except Exception as e:
        console.print(f"[red]Error generating demo: {e}[/red]")
        raise typer.Exit(code=1)


def _find_config_files(path: Path) -> list[Path]:
    """Find all YAML configuration files."""
    if path.is_file():
        return [path]
    
    files = []
    for ext in ["*.yaml", "*.yml"]:
        files.extend(path.rglob(ext))
    
    return sorted(files)


def main():
    app()


if __name__ == "__main__":
    main()
