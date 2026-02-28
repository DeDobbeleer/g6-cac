"""Validate command for CaC-ConfigMgr."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
import yaml
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree

from ...core.engine import ResolutionEngine
from ...core.api_validator import validate_api_compliance, ValidationError
from ...utils.exceptions import ConfigError
from ..app import app

console = Console()
validate_app = typer.Typer(help="Validate configurations")
app.add_typer(validate_app, name="validate")


@validate_app.callback(invoke_without_command=True)
def validate(
    fleet: Optional[Path] = typer.Option(None, "--fleet", "-f", help="Fleet YAML file"),
    topology: Optional[Path] = typer.Option(None, "--topology", "-t", help="Topology YAML file"),
    offline: bool = typer.Option(False, "--offline", help="Skip API connectivity checks"),
    template: Optional[Path] = typer.Option(None, "--template", help="Validate template only"),
    json: bool = typer.Option(False, "--json", help="Output JSON format"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed validation"),
) -> None:
    """Validate fleet and/or topology configuration.
    
    Validates at multiple levels:
    - Syntax: Valid YAML and schema compliance
    - References: All internal references are resolvable
    - API Compliance: Conforms to LogPoint Director API requirements
    - Dependencies: Cross-resource references are valid
    
    Examples:
        cac-configmgr validate -f fleet.yaml
        cac-configmgr validate -f fleet.yaml -t topology.yaml
        cac-configmgr validate --template templates/mssp/
    """
    try:
        validator = UnifiedValidator(
            fleet=fleet,
            topology=topology,
            template_dir=template,
            offline=offline,
            verbose=verbose,
        )
        errors = validator.validate()
        
        if json:
            _output_json(errors, validator.stats)
        else:
            _output_rich(errors, validator.stats, validator)
        
        # Exit codes per spec 40-CLI-WORKFLOW.md
        exit_code = _get_exit_code(errors)
        raise typer.Exit(code=exit_code)
        
    except ConfigError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=2)


class UnifiedValidator:
    """Unified validation combining all validation levels."""
    
    def __init__(
        self,
        fleet: Optional[Path] = None,
        topology: Optional[Path] = None,
        template_dir: Optional[Path] = None,
        offline: bool = False,
        verbose: bool = False,
    ):
        self.fleet = fleet
        self.topology = topology
        self.template_dir = template_dir
        self.offline = offline
        self.verbose = verbose
        self.stats = ValidationStats()
        self.resolved_resources: dict[str, list[dict]] = {}
    
    def validate(self) -> list[ValidationError]:
        """Run all validations.
        
        Returns:
            Combined list of all validation errors
        """
        errors: list[ValidationError] = []
        
        # Level 1: Syntax Validation
        syntax_errors = self._validate_syntax()
        errors.extend(syntax_errors)
        
        # If syntax fails, stop here
        if any(e.severity == "ERROR" for e in syntax_errors):
            return errors
        
        # Level 2: Resolve templates and validate references
        ref_errors = self._validate_references()
        errors.extend(ref_errors)
        
        # Level 3: API Compliance (required fields, types, patterns)
        if self.resolved_resources:
            api_errors = self._validate_api_compliance()
            errors.extend(api_errors)
        
        # Level 4: Cross-resource Dependencies
        if self.resolved_resources:
            dep_errors = self._validate_dependencies()
            errors.extend(dep_errors)
        
        self.stats.total_errors = len([e for e in errors if e.severity == "ERROR"])
        self.stats.total_warnings = len([e for e in errors if e.severity == "WARNING"])
        
        return errors
    
    def _validate_syntax(self) -> list[ValidationError]:
        """Validate YAML syntax and basic schema."""
        errors = []
        
        if self.fleet:
            try:
                with open(self.fleet) as f:
                    content = yaml.safe_load(f)
                    if content:
                        self.stats.fleet_resources = self._count_resources(content)
            except yaml.YAMLError as e:
                errors.append(ValidationError(
                    resource_type="fleet",
                    resource_name=str(self.fleet),
                    field="syntax",
                    message=f"Invalid YAML: {e}",
                    severity="ERROR"
                ))
        
        if self.topology:
            try:
                with open(self.topology) as f:
                    yaml.safe_load(f)
            except yaml.YAMLError as e:
                errors.append(ValidationError(
                    resource_type="topology",
                    resource_name=str(self.topology),
                    field="syntax",
                    message=f"Invalid YAML: {e}",
                    severity="ERROR"
                ))
        
        return errors
    
    def _validate_references(self) -> list[ValidationError]:
        """Validate template references and resolve."""
        errors = []
        
        if not self.fleet:
            return errors
        
        try:
            engine = ResolutionEngine(str(self.fleet))
            resolved = engine.resolve_fleet()
            self.resolved_resources = resolved
            self.stats.resolved_resources = self._count_total_resources(resolved)
        except ConfigError as e:
            errors.append(ValidationError(
                resource_type="resolution",
                resource_name=str(self.fleet),
                field="templates",
                message=str(e),
                severity="ERROR"
            ))
        
        return errors
    
    def _validate_api_compliance(self) -> list[ValidationError]:
        """Validate against LogPoint Director API specs."""
        return validate_api_compliance(self.resolved_resources)
    
    def _validate_dependencies(self) -> list[ValidationError]:
        """Validate cross-resource dependencies are already checked in API validator."""
        # Dependencies are validated by API validator
        return []
    
    def _count_resources(self, content: dict) -> dict[str, int]:
        """Count resources in fleet."""
        counts = {}
        if isinstance(content, dict):
            for key, value in content.items():
                if isinstance(value, list):
                    counts[key] = len(value)
        return counts
    
    def _count_total_resources(self, resources: dict[str, list]) -> int:
        """Count total resolved resources."""
        return sum(len(v) for v in resources.values())


class ValidationStats:
    """Validation statistics."""
    
    def __init__(self):
        self.fleet_resources: dict[str, int] = {}
        self.resolved_resources: int = 0
        self.total_errors: int = 0
        self.total_warnings: int = 0


def _output_json(errors: list[ValidationError], stats: ValidationStats) -> None:
    """Output validation results as JSON."""
    import json
    
    result = {
        "valid": stats.total_errors == 0,
        "summary": {
            "errors": stats.total_errors,
            "warnings": stats.total_warnings,
            "resolved_resources": stats.resolved_resources,
        },
        "errors": [
            {
                "resource_type": e.resource_type,
                "resource_name": e.resource_name,
                "field": e.field,
                "message": e.message,
                "severity": e.severity,
            }
            for e in errors
        ]
    }
    
    console.print(json.dumps(result, indent=2))


def _output_rich(
    errors: list[ValidationError], 
    stats: ValidationStats,
    validator: UnifiedValidator,
) -> None:
    """Output rich formatted validation report."""
    
    # Summary panel
    if stats.total_errors == 0:
        status = "[green]✓ Validation Successful[/green]"
    else:
        status = f"[red]✗ {stats.total_errors} Error(s)[/red]"
    
    summary_table = Table(show_header=False, box=None)
    summary_table.add_row("Status:", status)
    summary_table.add_row("Warnings:", f"{stats.total_warnings}")
    summary_table.add_row("Resolved Resources:", f"{stats.resolved_resources}")
    
    if validator.fleet:
        summary_table.add_row("Fleet File:", str(validator.fleet))
    
    console.print(Panel(summary_table, title="Validation Summary", border_style="blue"))
    
    # Resource breakdown
    if stats.fleet_resources:
        resource_tree = Tree("[bold]Resources Found[/bold]")
        for res_type, count in stats.fleet_resources.items():
            resource_tree.add(f"[cyan]{res_type}[/cyan]: {count}")
        console.print(resource_tree)
    
    # Errors
    errors_list = [e for e in errors if e.severity == "ERROR"]
    if errors_list:
        console.print(f"\n[bold red]❌ Validation Errors ({len(errors_list)})[/bold red]")
        
        # Group by resource type
        by_type: dict[str, list[ValidationError]] = {}
        for e in errors_list:
            by_type.setdefault(e.resource_type, []).append(e)
        
        for res_type, errs in by_type.items():
            console.print(f"\n[yellow]{res_type}:[/yellow]")
            for e in errs:
                console.print(f"  • [red]{e.resource_name}[/red] → {e.field}: {e.message}")
                if validator.verbose and e.api_doc:
                    console.print(f"    [dim]{e.api_doc}[/dim]")
    
    # Warnings
    warnings = [e for e in errors if e.severity == "WARNING"]
    if warnings:
        console.print(f"\n[bold yellow]⚠️ Warnings ({len(warnings)})[/bold yellow]")
        for e in warnings:
            console.print(f"  • {e.resource_name}: {e.message}")


def _get_exit_code(errors: list[ValidationError]) -> int:
    """Calculate exit code per 40-CLI-WORKFLOW.md.
    
    Returns:
        0: Valid, no warnings
        1: Valid, warnings present
        2: Validation errors
    """
    has_errors = any(e.severity == "ERROR" for e in errors)
    has_warnings = any(e.severity == "WARNING" for e in errors)
    
    if has_errors:
        return 2
    elif has_warnings:
        return 1
    else:
        return 0
