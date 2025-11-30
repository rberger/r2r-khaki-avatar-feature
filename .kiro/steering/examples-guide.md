---
title: TC Examples Guide
inclusion: always
---

# Examples Directory Guide

The tc-functors examples are available in the main tc repository at:
**https://github.com/tc-functors/tc/tree/main/examples**

These reference implementations demonstrate tc patterns and capabilities.

## Directory Structure

### [examples/apps/](https://github.com/tc-functors/tc/tree/main/examples/apps)

Complete application examples:

- **[chat](https://github.com/tc-functors/tc/tree/main/examples/apps/chat)**: Real-time chat using channels (WebSocket)
- **[notes](https://github.com/tc-functors/tc/tree/main/examples/apps/notes)**: Full-stack app with GraphQL mutations, subscriptions, and SPA

### [examples/composition/](https://github.com/tc-functors/tc/tree/main/examples/composition)

Entity composition patterns showing how different entities connect:

- **[event-channel](https://github.com/tc-functors/tc/tree/main/examples/composition/event-channel)**: Event triggering channel
- **[event-function](https://github.com/tc-functors/tc/tree/main/examples/composition/event-function)**: Event triggering function
- **[event-mutation](https://github.com/tc-functors/tc/tree/main/examples/composition/event-mutation)**: Event triggering GraphQL mutation
- **[event-state](https://github.com/tc-functors/tc/tree/main/examples/composition/event-state)**: Event triggering Step Functions workflow
- **[function-event](https://github.com/tc-functors/tc/tree/main/examples/composition/function-event)**: Function triggering event
- **[function-function](https://github.com/tc-functors/tc/tree/main/examples/composition/function-function)**: Function chaining
- **[function-mutation](https://github.com/tc-functors/tc/tree/main/examples/composition/function-mutation)**: Function triggering mutation
- **[mutation-function](https://github.com/tc-functors/tc/tree/main/examples/composition/mutation-function)**: Mutation resolver calling function
- **[queue-state](https://github.com/tc-functors/tc/tree/main/examples/composition/queue-state)**: Queue triggering state machine
- **route-***: Various route compositions

### [examples/functions/](https://github.com/tc-functors/tc/tree/main/examples/functions)

Function runtime examples:

- **[clojure-inline](https://github.com/tc-functors/tc/tree/main/examples/functions/clojure-inline)**, **[janet-inline](https://github.com/tc-functors/tc/tree/main/examples/functions/janet-inline)**: Alternative language runtimes
- **[node-basic](https://github.com/tc-functors/tc/tree/main/examples/functions/node-basic)**, **[node-inline](https://github.com/tc-functors/tc/tree/main/examples/functions/node-inline)**: Node.js functions
- **[python-basic](https://github.com/tc-functors/tc/tree/main/examples/functions/python-basic)**, **[python-inline](https://github.com/tc-functors/tc/tree/main/examples/functions/python-inline)**, **[python-image](https://github.com/tc-functors/tc/tree/main/examples/functions/python-image)**, **[python-layer](https://github.com/tc-functors/tc/tree/main/examples/functions/python-layer)**, **[python-snap](https://github.com/tc-functors/tc/tree/main/examples/functions/python-snap)**: Python variants
- **[ruby-basic](https://github.com/tc-functors/tc/tree/main/examples/functions/ruby-basic)**, **[ruby-inline](https://github.com/tc-functors/tc/tree/main/examples/functions/ruby-inline)**: Ruby functions
- **[rust-inline](https://github.com/tc-functors/tc/tree/main/examples/functions/rust-inline)**: Rust functions
- **[mixed](https://github.com/tc-functors/tc/tree/main/examples/functions/mixed)**: Multiple languages in one topology
- **[infra-basic](https://github.com/tc-functors/tc/tree/main/examples/functions/infra-basic)**: Custom infrastructure configuration

### [examples/patterns/](https://github.com/tc-functors/tc/tree/main/examples/patterns)

Common application patterns:

- **[chat](https://github.com/tc-functors/tc/tree/main/examples/patterns/chat)**: WebSocket-based real-time chat
- **[evented](https://github.com/tc-functors/tc/tree/main/examples/patterns/evented)**: Event-driven architecture
- **[gql-progress](https://github.com/tc-functors/tc/tree/main/examples/patterns/gql-progress)**, **[gql-proxy](https://github.com/tc-functors/tc/tree/main/examples/patterns/gql-proxy)**: GraphQL patterns
- **[htmx](https://github.com/tc-functors/tc/tree/main/examples/patterns/htmx)**: HTMX server-side rendering
- **[http-upload](https://github.com/tc-functors/tc/tree/main/examples/patterns/http-upload)**: File upload handling
- **[rest-async](https://github.com/tc-functors/tc/tree/main/examples/patterns/rest-async)**, **[rest-async-progress](https://github.com/tc-functors/tc/tree/main/examples/patterns/rest-async-progress)**: Async REST APIs
- **[rest-auth](https://github.com/tc-functors/tc/tree/main/examples/patterns/rest-auth)**: Authentication patterns

### [examples/states/](https://github.com/tc-functors/tc/tree/main/examples/states)

Step Functions workflow patterns:

- **[basic](https://github.com/tc-functors/tc/tree/main/examples/states/basic)**: Simple state machine
- **[continuation](https://github.com/tc-functors/tc/tree/main/examples/states/continuation)**: Long-running workflows
- **[map-async](https://github.com/tc-functors/tc/tree/main/examples/states/map-async)**, **[map-csv](https://github.com/tc-functors/tc/tree/main/examples/states/map-csv)**, **[map-dist](https://github.com/tc-functors/tc/tree/main/examples/states/map-dist)**: Map state patterns
- **[mapreduce](https://github.com/tc-functors/tc/tree/main/examples/states/mapreduce)**: MapReduce pattern
- **[parallel](https://github.com/tc-functors/tc/tree/main/examples/states/parallel)**: Parallel execution
- **[routing](https://github.com/tc-functors/tc/tree/main/examples/states/routing)**: Conditional routing

### [examples/pages/](https://github.com/tc-functors/tc/tree/main/examples/pages)

Static site and SPA examples:

- **[static](https://github.com/tc-functors/tc/tree/main/examples/pages/static)**: Basic static site
- **[spa-mithril](https://github.com/tc-functors/tc/tree/main/examples/pages/spa-mithril)**, **[spa-svelte](https://github.com/tc-functors/tc/tree/main/examples/pages/spa-svelte)**: Single-page applications
- **[pwa](https://github.com/tc-functors/tc/tree/main/examples/pages/pwa)**: Progressive web app

### [examples/orchestrator/](https://github.com/tc-functors/tc/tree/main/examples/orchestrator)

Complex orchestration examples with multiple functions coordinating

### [examples/tables/](https://github.com/tc-functors/tc/tree/main/examples/tables)

Database/table schema examples

### [examples/tests/](https://github.com/tc-functors/tc/tree/main/examples/tests)

Testing patterns and examples

## Using Examples

1. **Browse by use case**: Find the pattern closest to your needs
2. **Study the topology.yml**: Understand entity relationships
3. **Check function handlers**: See implementation patterns
4. **Adapt to your needs**: Copy and modify for your application

## Key Files in Examples

- **topology.yml**: Main topology specification
- **function.yml**: Function-specific configuration (optional)
- **handler.{py,js,rb,rs}**: Function implementation
- **index.html**: Frontend for full-stack examples
- **package.json**, **pyproject.toml**, **Gemfile**, **Cargo.toml**: Language-specific dependencies
