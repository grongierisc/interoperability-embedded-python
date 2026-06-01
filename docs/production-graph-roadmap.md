# Production Graph Roadmap And Gaps

## Summary

`Production` is the Python authoring DSL for interoperability production
topology. It owns the Python-authored graph: items, ports, settings, and
connections.

Python `Production` is the source of truth for Python-authored topology. IRIS
remains the runtime source of truth. Imported graphs are operational
reconstructions until metadata persistence makes round-trip fidelity possible.

An IRIS production topology can be modeled as a directed multigraph of possible
communication routes. These route edges are not DAG execution dependencies.

The long-term direction is for the Python `Production` graph to generate the
IRIS production definition, while IRIS runtime export and `OnGetConnections`
provide operational import and compatibility.

## Current State

Implemented graph authoring:

- `Production`
- `ComponentRef`
- `Port`
- `target()`
- `prod.service(...)`
- `prod.process(...)`
- `prod.operation(...)`
- `prod.connect(source_port, target_component)`

Implemented graph import and display:

- `Production.from_iris(name)`
- `Production.from_dict(data, connections=...)`
- `Production.item(name)`
- `Production.component_ref(target)`
- `Production.get_component(target)`
- `ComponentRef.port(name, logical_name="")`
- `Production.graph()`
- `Production.diff(other=None)`
- `Production.graph_diff(other=None)`
- `ProductionGraph.to_dict()`
- printable graph text through `str(prod.graph())`

`str(port)` returns the stable authoring identity, such as `FileInput.Output`.
Runtime dispatch uses explicit port resolution.

Implemented production lifecycle:

- `prod.start()`
- `prod.stop()`
- `prod.restart()`
- `prod.kill()`
- `prod.status()`
- `prod.queue()`
- `prod.update()`
- `prod.export()`
- `prod.test(...)`
- `prod.log()`
- `prod.set_default()`
- `prod.inspect_component(...)`
- `prod.start_component(...)`
- `prod.stop_component(...)`
- `prod.restart_component(...)`
- `prod.test_component(...)`

Lifecycle methods that mutate the current runtime production verify that IRIS
currently points at the same production object before calling the underlying
IRIS operation.

`prod.test_component("Item.Port", message)` resolves from the current Python
object graph. It does not silently fall back to IRIS export. Existing deployed
productions should be reconstructed explicitly with `Production.from_iris(...)`
before testing by port path. Runtime status checks fail closed when the current
production cannot be verified. `prod.test(...)` remains a compatibility alias.

`ComponentRef` exposes convenience methods that delegate to its owning
production: `inspect()`, `start()`, `stop()`, `restart()`, and `test(...)`.
It is a Python handle to a configured production item, not the live IRIS host
instance.

Implemented graph-local editing:

- `prod.add_component(...)`
- `prod.update_component(...)`
- `prod.delete_component(...)`
- `prod.disconnect(...)`
- `prod.sync()` / `prod.apply()` for explicit local IRIS registration

Implemented diffing:

- `prod.diff()` compares the desired Python definition with the deployed IRIS
  operational reconstruction.
- `prod.diff(other_prod)` compares with another `Production`.
- `prod.diff(exported_dict)` compares with an exported production dictionary.
- The diff is directional: changes describe what must change in the
  current/imported state to match the Python `Production` object.
- `prod.graph_diff(...)` includes route metadata such as edge origin and
  interaction. `prod.diff(...)` remains the deployable IRIS-shape diff.

## IRIS Graph Import

The import path uses two sources:

1. Exported production definition
   - Provides items, classes, settings, pool size, enabled state, schedule, and
     production-level attributes.
2. Runtime connection discovery
   - Uses IRIS `OnGetConnections` through `Ens.Config.Production.GetConnections`.
   - Works for generated Python proxy classes, ObjectScript classes, built-in
     `Ens.Host` components, and classes extending `IOP.Common`.

`OnGetConnections` is the primary graph source when available. If runtime
connection discovery fails for an item, the importer falls back to Host settings
whose value names another production item. When runtime discovery reports no
targets for an item, Host settings are still used to draw inferred possible
routes.

Queue metadata is imported separately through `Ens.Queue.GetCount(item.Name)`.
It is runtime production information, not authoring graph data. It is exposed
through `prod.queue()`, cached separately from the topology graph, and is not
serialized into the production definition. `prod.queue_info()` remains available
as a compatibility alias.

## Python And ObjectScript Components

Python-authored components use Python classes:

```python
prod = Production("Demo.Production")
file = prod.service("FileInput", FileService)
orders = prod.operation(OrderOperation)
prod.connect(file.Output, orders)
```

ObjectScript and built-in IRIS components use `class_name`:

```python
prod = Production("Demo.Production")
file = prod.service("FileIn", class_name="EnsLib.File.PassthroughService")
out = prod.operation("FileOut", class_name="EnsLib.File.PassthroughOperation")
prod.connect(file.port("TargetConfigNames"), out)
```

Rules:

- Python classes are registered during migration.
- `ComponentRef.component_class` is the Python business host implementation
  class, not the adapter class.
- `ComponentRef.adapter_class_name` exposes the configured adapter type when it
  is known from Python source or explicitly supplied metadata.
- Python adapter classes passed with `adapter_class=...` are registered during
  migration.
- `class_name` string components are not registered as Python components.
- ObjectScript classes must already exist in IRIS or be loaded through existing
  `.cls` migration support.
- Manual ports are required when Python has no `target()` descriptor.

## Roadmap

### Phase 1: Solidify Graph Import

- Add more e2e coverage for `Production.from_iris(...)`.
- Validate graph import against Python proxy classes and ObjectScript classes.
- Improve warning messages for runtime-only and unresolved edges.
- Keep settings fallback for environments where `OnGetConnections` is not
  available.

### Phase 2: Persist IOP Graph Metadata

Persist IOP-owned metadata so Python-to-IRIS-to-Python round trips lose less
intent:

- logical `target("orders")` names
- declared port names and types
- richer route intent beyond the current origin/interaction metadata
- Python source module and class origin
- runtime-only edges
- unresolved graph warnings

Without this metadata, IRIS can reconstruct operational topology but not the
original Python authoring intent.

### Phase 3: Add Graph Apply

Graph diff exists in two forms today: deployable `prod.diff(...)` and metadata-
aware `prod.graph_diff(...)`. The missing piece is explicit graph apply:

- show additions, updates, removals, and changed settings
- apply changes only when explicitly requested
- avoid hidden runtime mutation from simple Python object edits

This should become the safe path for component-level CRUD.

### Phase 4: Improve ObjectScript Introspection

Use IRIS class metadata to improve non-Python support:

- discover settings and controls from ObjectScript classes
- identify `Ens.DataType.ConfigName` settings as candidate ports
- expose setting metadata in `ProductionGraph`
- distinguish static, dynamic, and conditional runtime connections

### Phase 5: Make Graph The Orchestration Backbone

Use `ProductionGraph` as the backbone for:

- visual graph display
- production validation
- request routing
- workflow/orchestration integration
- graph projection for DAG-compatible subsets
- IRIS XML generation
- future non-IRIS execution backends

At this stage, the graph becomes the canonical design artifact and IRIS
production XML becomes one generated output.

## Gaps

### Metadata Gaps

- IRIS export does not preserve Python class objects.
- IRIS export does not preserve logical names from `target("orders")`.
- IRIS export does not preserve the Python module/class origin unless stored as
  explicit metadata.
- `OnGetConnections` usually returns target names, not always source port names.
- Runtime-discovered edges may not map cleanly to a specific `Port`.

### Runtime Graph Gaps

- Conditional routing may depend on message content and cannot always be
  represented as one static route edge.
- BPL, DTL, routing rules, and business rule classes need specialized graph
  import.
- Dynamic targets can be visible at runtime but not fully recoverable as
  design-time graph intent.
- A production must be compiled and available in IRIS for runtime connection
  discovery.
- Queue counts are point-in-time runtime counters and can change immediately
  after they are fetched.
- Current queue support reports item queue counts, not full queue browser data
  such as active message details or retry controls.

### Sync Gaps

- `prod.sync()` currently registers the full current production definition
  locally; it is not yet a fine-grained graph diff.
- Remote sync still belongs to migration because remote registration also needs
  source upload.
- Component add/update/delete are graph-local edits until explicitly applied.
- Delete safety needs policy for running productions, queued messages, and
  dependent routing.

### ObjectScript Gaps

- ObjectScript source code is not reconstructed from production export.
- Built-in and ObjectScript classes need manual ports unless IRIS setting
  introspection is added.
- Existing ObjectScript classes may implement custom `OnGetConnections`
  behavior that reports runtime targets without exposing source setting names.

## Source Of Truth Decision

Python `Production` graph is the intended future source of truth for
Python-authored design-time topology.

IRIS remains authoritative for:

- runtime state
- deployed compiled classes
- queues and jobs
- logs
- current production status
- legacy production definitions

The transition is complete only when graph metadata persistence and graph
diff/apply can round-trip Python and IRIS production definitions without losing
important design intent.
