"""Plan command for CaC-ConfigMgr.

Shows the diff between declared state (YAML) and actual state (API).
Works with both Director and Direct modes.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from ..factory import ProviderFactory, create_provider
from ...core.engine import ResolutionEngine
from ...core.planner import DiffCalculator, ResourceChange, ChangeType
from ...utils.exceptions import ConfigError

console = Console()


def plan(
    fleet: Path = typer.Option(..., "--fleet", "-f", help="Fleet YAML file"),
    topology: Optional[Path] = typer.Option(None, "--topology", "-t", help="Topology YAML file"),
    config: Optional[Path] = typer.Option(None, "--config", "-c", help="Provider config file"),
    mode: Optional[str] = typer.Option(None, "--mode", "-m", help="Override mode (director/direct)"),
    detailed: bool = typer.Option(False, "--detailed", "-d", help="Show field-level diff"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output JSON format"),
    target_node: Optional[str] = typer.Option(None, "--target-node", help="Target specific node (Direct mode)"),
) -> None:
    """Plan changes between declared and actual state.
    
    Compares the desired state defined in YAML files with the actual state
    in LogPoint Director or SIEM nodes.
    
    Examples:
        # Director mode with config file
        cac-configmgr plan -f fleet.yaml -t topology.yaml -c config.yaml
        
        # Direct mode (multi-node)
        cac-configmgr plan -f fleet.yaml -c nodes.yaml
        
        # Target specific node
        cac-configmgr plan -f fleet.yaml -c nodes.yaml --target-node siem-prod-01
        
        # Detailed output
        cac-configmgr plan -f fleet.yaml -t topology.yaml --detailed
    """
    try:
        # 1. Load configuration
        if config:
            factory = ProviderFactory.from_file(config)
        else:
            factory = ProviderFactory.from_env(mode=mode)  # type: ignore
        
        console.print(f"[dim]Mode: {factory.get_mode()}[/dim]")
        
        # 2. Load declared state
        console.print("[dim]Loading declared state from YAML...[/dim]")
        engine = ResolutionEngine(str(fleet))
        declared = engine.resolve()
        
        # 3. Fetch actual state based on mode
        if factory.get_mode() == "director":
            plan_director(factory, declared, detailed, json_output)
        else:
            plan_direct(factory, declared, target_node, detailed, json_output)
        
    except ConfigError as e:
        console.print(f"[red]Configuration error: {e}[/red]")
        raise typer.Exit(code=2)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=3)


def plan_director(
    factory: ProviderFactory,
    declared,
    detailed: bool,
    json_output: bool,
) -> None:
    """Plan for Director mode."""
    import asyncio
    asyncio.run(_plan_director_async(factory, declared, detailed, json_output))


async def _plan_director_async(
    factory: ProviderFactory,
    declared,
    detailed: bool,
    json_output: bool,
) -> None:
    """Async plan for Director mode."""
    console.print("[dim]Connecting to Director...[/dim]")
    
    async with factory.create_director() as provider:
        # Fetch actual state
        console.print("[dim]Fetching actual state from Director...[/dim]")
        actual = {}
        for resource_type in declared.resources.keys():
            try:
                actual[resource_type] = await provider.get_resources(resource_type)
            except Exception as e:
                console.print(f"[yellow]Warning: Could not fetch {resource_type}: {e}[/yellow]")
                actual[resource_type] = []
        
        # Calculate diff
        convention = provider.get_convention()
        calculator = DiffCalculator(convention)
        plan = calculator.compare(declared.resources, actual)
        
        # Output
        if json_output:
            _output_json(plan)
        else:
            _output_table(plan, detailed)


def plan_direct(
    factory: ProviderFactory,
    declared,
    target_node: Optional[str],
    detailed: bool,
    json_output: bool,
) -> None:
    """Plan for Direct mode."""
    import asyncio
    asyncio.run(_plan_direct_async(factory, declared, target_node, detailed, json_output))


async def _plan_direct_async(
    factory: ProviderFactory,
    declared,
    target_node: Optional[str],
    detailed: bool,
    json_output: bool,
) -> None:
    """Async plan for Direct mode."""
    from cac_configmgr.providers.direct import MultiNodeProvider
    
    node_ids = factory.get_node_ids()
    console.print(f"[dim]Nodes: {', '.join(node_ids)}[/dim]")
    
    # If targeting specific node, filter
    if target_node and target_node not in node_ids:
        console.print(f"[red]Error: Node '{target_node}' not found in config[/red]")
        raise typer.Exit(code=2)
    
    # Multi-node comparison
    async with factory.create_multi_node() as multi:
        all_plans = {}
        
        for provider in multi.providers:
            node_id = provider.config.node_id
            
            if target_node and node_id != target_node:
                continue
            
            console.print(f"[dim]Checking node: {node_id}...[/dim]")
            
            try:
                actual = {}
                for resource_type in declared.resources.keys():
                    try:
                        actual[resource_type] = await provider.get_resources(resource_type)
                    except Exception as e:
                        console.print(f"[yellow]  Warning: Could not fetch {resource_type}: {e}[/yellow]")
                        actual[resource_type] = []
                
                convention = provider.get_convention()
                calculator = DiffCalculator(convention)
                plan = calculator.compare(declared.resources, actual)
                all_plans[node_id] = plan
                
            except Exception as e:
                console.print(f"[red]  Error connecting to {node_id}: {e}[/red]")
                all_plans[node_id] = None
        
        # Output
        if json_output:
            _output_json_multi(all_plans)
        else:
            _output_table_multi(all_plans, detailed)


def _output_table(plan: DiffCalculator, detailed: bool) -> None:
    """Output plan as Rich table."""
    if plan.is_empty():
        console.print("[green]✓ No changes needed - actual state matches declared state[/green]")
        return
    
    console.print(f"\n[bold]Plan: {plan.summary}[/bold]\n")
    
    for resource_type, changes in plan.changes_by_type().items():
        table = Table(title=f"{resource_type.replace('_', ' ').title()}")
        table.add_column("Action", style="bold")
        table.add_column("Name")
        table.add_column("Details")
        
        for change in changes:
            action_style = {
                ChangeType.CREATE: "green",
                ChangeType.UPDATE: "yellow",
                ChangeType.DELETE: "red",
                ChangeType.UNCHANGED: "dim",
            }.get(change.change_type, "white")
            
            action_symbol = {
                ChangeType.CREATE: "+",
                ChangeType.UPDATE: "~",
                ChangeType.DELETE: "-",
                ChangeType.UNCHANGED: "=",
            }.get(change.change_type, "?")
            
            details = ""
            if detailed and change.diffs:
                details = "\n".join(f"  {d.field}: {d.old} → {d.new}" for d in change.diffs[:3])
            elif change.diffs:
                details = f"{len(change.diffs)} fields changed"
            
            table.add_row(
                f"[{action_style}]{action_symbol} {change.change_type.name}[/{action_style}]",
                change.name,
                details
            )
        
        console.print(table)
        console.print()


def _output_json(plan: DiffCalculator) -> None:
    """Output plan as JSON."""
    import json
    console.print(json.dumps(plan.to_dict(), indent=2))


def _output_table_multi(all_plans: dict, detailed: bool) -> None:
    """Output multi-node plan."""
    for node_id, plan in all_plans.items():
        console.print(f"\n[bold cyan]Node: {node_id}[/bold cyan]")
        if plan is None:
            console.print("[red]  Connection failed[/red]")
            continue
        _output_table(plan, detailed)


def _output_json_multi(all_plans: dict) -> None:
    """Output multi-node plan as JSON."""
    import json
    result = {
        node_id: plan.to_dict() if plan else {"error": "Connection failed"}
        for node_id, plan in all_plans.items()
    }
    console.print(json.dumps(result, indent=2))
