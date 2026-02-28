"""CLI entry point for CaC-ConfigMgr."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich import box

from ..utils import load_yaml, load_instance, load_fleet, load_multi_file_template, YamlError
from ..core import (
    ResolutionEngine, 
    filter_internal_ids, 
    ConsistencyValidator, 
    LogPointDependencyValidator,
    validate_api_compliance,
    ValidationError as APIValidationError,
)

app = typer.Typer(help="Configuration as Code Manager for LogPoint")
console = Console()


@app.command()
def validate(
    config_path: Path = typer.Argument(..., help="Path to config file or directory"),
    fleet: Optional[Path] = typer.Option(None, "--fleet", "-f", help="Fleet YAML file for full validation"),
    topology: Optional[Path] = typer.Option(None, "--topology", "-t", help="Topology YAML file for dependency validation"),
    api_compliance: bool = typer.Option(True, "--api-compliance/--no-api", help="Validate against LogPoint Director API"),
    offline: bool = typer.Option(False, "--offline", help="Skip API connectivity checks"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
    json_output: bool = typer.Option(False, "--json", help="Output JSON format"),
):
    """Validate configuration with comprehensive checks.
    
    Performs multi-level validation:
    1. Syntax: Valid YAML and schema compliance
    2. References: All internal references are resolvable  
    3. API Compliance: Conforms to LogPoint Director API requirements
    4. Dependencies: Cross-resource references are valid
    
    Examples:
        cac-configmgr validate configs/
        cac-configmgr validate -f fleet.yaml -t topology.yaml --verbose
        cac-configmgr validate instances/bank-a/prod/ --api-compliance
    """
    console.print(f"[bold blue]Validating {config_path}...[/bold blue]\n")
    
    # Level 1: Syntax Validation
    files = _find_config_files(config_path)
    if not files:
        console.print("[red]No configuration files found.[/red]")
        raise typer.Exit(code=2)
    
    syntax_errors = []
    warnings = 0
    
    for file in files:
        try:
            data = load_yaml(file)
            kind = data.get("kind", "Unknown")
            
            # Try to validate based on kind
            if kind == "Fleet":
                load_fleet(file)
            elif kind == "ConfigTemplate":
                load_multi_file_template(file.parent if file.parent.name else file)
            elif kind == "TopologyInstance":
                load_instance(file)
            else:
                warnings += 1
                if verbose:
                    console.print(f"[yellow]⚠ Unknown kind in {file}: {kind}[/yellow]")
                
        except YamlError as e:
            syntax_errors.append(f"{file}: {e}")
        except Exception as e:
            syntax_errors.append(f"{file}: {e}")
    
    if syntax_errors:
        console.print(f"[bold red]❌ Syntax Errors ({len(syntax_errors)}):[/bold red]")
        for err in syntax_errors:
            console.print(f"  • {err}")
        console.print()
        raise typer.Exit(code=2)
    
    console.print(f"[green]✓ Syntax validation passed[/green] ({len(files)} files)")
    console.print()
    
    # Level 2-4: Full validation with fleet and topology
    all_errors: list[APIValidationError] = []
    resolved_resources: dict[str, list[dict]] = {}
    
    if fleet:
        try:
            # Load fleet and resolve templates
            console.print("[dim]Resolving template chain...[/dim]")
            
            if topology:
                # Use ResolutionEngine with topology for full resolution
                # Templates are in demo-configs/templates/
                templates_dir = Path(fleet).parent.parent.parent.parent / "templates"
                if not templates_dir.exists():
                    # Fallback: try to find templates directory
                    templates_dir = Path("demo-configs/templates")
                engine = ResolutionEngine(templates_dir)
                instance = load_instance(topology)
                resolved = engine.resolve(instance)
                resolved_resources = resolved.resources
            else:
                # Just load fleet directly without template resolution
                fleet_config = load_fleet(fleet)
                # Extract resources from fleet spec
                resolved_resources = {}
                if fleet_config.spec:
                    if hasattr(fleet_config.spec, 'repos'):
                        resolved_resources['repos'] = [
                            r.model_dump(by_alias=True) if hasattr(r, 'model_dump') else r
                            for r in fleet_config.spec.repos
                        ]
                    if hasattr(fleet_config.spec, 'routing_policies'):
                        resolved_resources['routing_policies'] = [
                            r.model_dump(by_alias=True) if hasattr(r, 'model_dump') else r
                            for r in fleet_config.spec.routing_policies
                        ]
                    if hasattr(fleet_config.spec, 'processing_policies'):
                        resolved_resources['processing_policies'] = [
                            r.model_dump(by_alias=True) if hasattr(r, 'model_dump') else r
                            for r in fleet_config.spec.processing_policies
                        ]
                    if hasattr(fleet_config.spec, 'normalization_policies'):
                        resolved_resources['normalization_policies'] = [
                            r.model_dump(by_alias=True) if hasattr(r, 'model_dump') else r
                            for r in fleet_config.spec.normalization_policies
                        ]
                    if hasattr(fleet_config.spec, 'enrichment_policies'):
                        resolved_resources['enrichment_policies'] = [
                            r.model_dump(by_alias=True) if hasattr(r, 'model_dump') else r
                            for r in fleet_config.spec.enrichment_policies
                        ]
            
            # Count resources
            total_resources = sum(len(v) for v in resolved_resources.values())
            console.print(f"[dim]  → Resolved {total_resources} resources[/dim]")
            console.print()
            
            # Level 3: API Compliance Validation
            if api_compliance and resolved_resources:
                console.print("[dim]Validating API compliance...[/dim]")
                api_errors = validate_api_compliance(resolved_resources)
                
                if api_errors:
                    # Filter to only API validation errors
                    api_errs = [e for e in api_errors]
                    all_errors.extend(api_errs)
                    console.print(f"[dim]  → {len(api_errs)} API validation issues[/dim]")
                else:
                    console.print("[dim]  → API compliance OK[/dim]")
                console.print()
            
            # Level 4: Cross-resource Dependencies
            if resolved_resources:
                console.print("[dim]Validating dependencies...[/dim]")
                
                # Use ConsistencyValidator
                consistency_val = ConsistencyValidator(resolved_resources)
                consistency_errors = consistency_val.validate()
                all_errors.extend([
                    APIValidationError(
                        resource_type=e.resource_type,
                        resource_name=e.resource_name,
                        field=e.field,
                        message=e.message,
                        severity="ERROR",
                    )
                    for e in consistency_errors
                ])
                
                # Use LogPointDependencyValidator
                dep_val = LogPointDependencyValidator(resolved_resources)
                dep_errors = dep_val.validate()
                all_errors.extend([
                    APIValidationError(
                        resource_type=e.resource_type,
                        resource_name=e.resource_name,
                        field="dependency",
                        message=e.message,
                        severity=e.severity,
                    )
                    for e in dep_errors
                ])
                
                if consistency_errors or dep_errors:
                    console.print(f"[dim]  → {len(consistency_errors) + len(dep_errors)} dependency issues[/dim]")
                else:
                    console.print("[dim]  → All dependencies valid[/dim]")
                console.print()
                
        except Exception as e:
            console.print(f"[red]Error during resolution: {e}[/red]")
            if verbose:
                import traceback
                console.print(traceback.format_exc())
            raise typer.Exit(code=2)
    
    # Output results
    if json_output:
        _output_validation_json(all_errors, warnings, len(files), resolved_resources)
    else:
        _output_validation_rich(all_errors, warnings, len(files), resolved_resources, verbose)
    
    # Exit codes per 40-CLI-WORKFLOW.md
    errors_list = [e for e in all_errors if e.severity == "ERROR"]
    warnings_list = [e for e in all_errors if e.severity == "WARNING"]
    
    if errors_list:
        console.print(f"\n[bold red]❌ Validation failed with {len(errors_list)} error(s)[/bold red]")
        raise typer.Exit(code=2)
    elif warnings_list or warnings > 0:
        console.print(f"\n[bold yellow]⚠ Validation passed with {len(warnings_list) + warnings} warning(s)[/bold yellow]")
        raise typer.Exit(code=1)
    else:
        console.print("\n[bold green]✓ All validations passed![/bold green]")
        raise typer.Exit(code=0)


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
        
        # Validate LogPoint dependencies (DirSync/API constraints)
        dep_validator = LogPointDependencyValidator(resolved.resources)
        dep_errors = dep_validator.validate()
        
        if dep_errors:
            # Group by severity
            errors = [e for e in dep_errors if e.severity == "ERROR"]
            warnings = [e for e in dep_errors if e.severity == "WARNING"]
            
            if errors:
                console.print("[bold red]LogPoint Dependency Errors:[/bold red]")
                for error in errors:
                    console.print(f"  [red]•[/red] {error.resource_type}.{error.resource_name}: {error.message}")
                console.print()
            
            if warnings:
                console.print("[bold yellow]LogPoint Dependency Warnings:[/bold yellow]")
                for error in warnings:
                    console.print(f"  [yellow]•[/yellow] {error.resource_type}.{error.resource_name}: {error.message}")
                console.print()
            
            if errors:
                console.print("[red]❌ Deployment would fail - dependency errors must be fixed[/red]")
                console.print()
        else:
            console.print("[green]✓ All LogPoint dependencies satisfied[/green]")
            console.print()
        
        # Show deployment order
        console.print("[dim]Deployment order:[/dim]")
        order = " → ".join(dep_validator.get_deployment_order()[:6])  # Show first 6
        console.print(f"[dim]  {order} → ...[/dim]")
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


def _output_validation_rich(
    errors: list[APIValidationError],
    warnings: int,
    file_count: int,
    resolved_resources: dict[str, list[dict]],
    verbose: bool,
) -> None:
    """Output rich formatted validation report."""
    
    errors_list = [e for e in errors if e.severity == "ERROR"]
    warnings_list = [e for e in errors if e.severity == "WARNING"]
    
    if errors_list or warnings_list:
        # Errors by category
        by_type: dict[str, list[APIValidationError]] = {}
        for e in errors_list + warnings_list:
            by_type.setdefault(e.resource_type, []).append(e)
        
        # Display errors
        if errors_list:
            console.print(f"[bold red]❌ Validation Errors ({len(errors_list)}):[/bold red]")
            for res_type, errs in sorted(by_type.items()):
                res_errs = [e for e in errs if e.severity == "ERROR"]
                if res_errs:
                    console.print(f"\n[yellow]{res_type}:[/yellow]")
                    for e in res_errs[:10]:  # Show first 10
                        console.print(f"  • [red]{e.resource_name}[/red] → {e.field}: {e.message}")
                    if len(res_errs) > 10:
                        console.print(f"  ... and {len(res_errs) - 10} more")
        
        # Display warnings
        if warnings_list:
            console.print(f"\n[bold yellow]⚠ Validation Warnings ({len(warnings_list)}):[/bold yellow]")
            for res_type, errs in sorted(by_type.items()):
                res_warns = [e for e in errs if e.severity == "WARNING"]
                if res_warns:
                    console.print(f"\n[yellow]{res_type}:[/yellow]")
                    for e in res_warns[:5]:
                        console.print(f"  • {e.resource_name}: {e.message}")
    
    # Summary table
    total_resolved = sum(len(v) for v in resolved_resources.values())
    
    summary = Table(title="Validation Summary", box=box.ROUNDED)
    summary.add_column("Level", style="cyan")
    summary.add_column("Status", style="green")
    summary.add_column("Details", style="white")
    
    summary.add_row("1. Syntax", "[green]✓ OK[/green]", f"{file_count} files parsed")
    
    if resolved_resources:
        if errors_list:
            summary.add_row("2. API Compliance", "[red]✗ FAILED[/red]", f"{len(errors_list)} errors")
        else:
            summary.add_row("2. API Compliance", "[green]✓ OK[/green]", f"{total_resolved} resources validated")
        
        if warnings_list:
            summary.add_row("3. Dependencies", "[yellow]⚠ WARNINGS[/yellow]", f"{len(warnings_list)} warnings")
        else:
            summary.add_row("3. Dependencies", "[green]✓ OK[/green]", "All references valid")
    else:
        summary.add_row("2. API Compliance", "[dim]SKIPPED[/dim]", "No fleet provided")
        summary.add_row("3. Dependencies", "[dim]SKIPPED[/dim]", "No fleet provided")
    
    console.print()
    console.print(summary)


def _output_validation_json(
    errors: list[APIValidationError],
    warnings: int,
    file_count: int,
    resolved_resources: dict[str, list[dict]],
) -> None:
    """Output JSON validation report."""
    import json
    
    errors_list = [e for e in errors if e.severity == "ERROR"]
    warnings_list = [e for e in errors if e.severity == "WARNING"]
    
    result = {
        "valid": len(errors_list) == 0,
        "summary": {
            "syntax_files": file_count,
            "resolved_resources": sum(len(v) for v in resolved_resources.values()),
            "errors": len(errors_list),
            "warnings": len(warnings_list) + warnings,
        },
        "errors": [
            {
                "resource_type": e.resource_type,
                "resource_name": e.resource_name,
                "field": e.field,
                "message": e.message,
                "severity": e.severity,
            }
            for e in errors_list
        ],
        "warnings": [
            {
                "resource_type": e.resource_type,
                "resource_name": e.resource_name,
                "field": e.field,
                "message": e.message,
            }
            for e in warnings_list
        ],
    }
    
    console.print(json.dumps(result, indent=2))


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
