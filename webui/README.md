# CargoDash WebUI (preview)

Visual graph editor for CargoDash pipelines. Pure frontend, single-direction
codegen: design the DAG on a canvas, export `pipeline.py`, run it with the
`cargodash` Python package.

## Stack

- Vite + React 18 + TypeScript
- React Flow (canvas)
- Monaco Editor (user function bodies)
- Zustand (graph state)
- Tailwind (styling)

## Quick start

```bash
cd webui
npm install
npm run dev          # http://localhost:5173
```

## Remote server access

When `npm run dev` runs on a remote machine you reach via your editor's
port-forwarding feature, you'll hit the dev server through one of two
URL shapes depending on the editor / tunnel:

1. **Root subdomain**, e.g. `https://xxx-5173.<region>.devtunnels.ms/` —
   VS Code Tunnels / Cursor. The forwarded port is on its own subdomain;
   the app lives at the root path. Just works.
2. **Subpath proxy**, e.g. `https://<host>/<...>/proxy/5173/` —
   `code-server` and similar in-browser VS Code variants, JupyterHub
   gateways, etc. The dev server is mounted under a path prefix.

The subpath case is the one that bites you: an absolute asset URL like
`/src/main.tsx` in the served HTML resolves to `https://<host>/src/main.tsx`,
bypassing the `/<...>/proxy/5173/` prefix and 404'ing. We work around
this with `base: './'` in `vite.config.ts`, which makes all generated
asset URLs relative to the current page. Relative URLs resolve correctly
in both the subpath and root-subdomain cases, so the config is
universally safe — no toggle needed.

If `npm run dev` is bound to all interfaces and the cluster permits SSH,
classic SSH local port forwarding also works as a fallback:

```bash
# on your laptop
ssh -L 5173:127.0.0.1:5173 <user>@<remote-host>
```

then open `http://localhost:5173` in your laptop browser.

### HMR (optional)

Hot-module-reload uses a separate WebSocket channel that `base` does not
influence. Through a subpath proxy it may or may not survive — depends
on whether the proxy forwards WebSocket upgrades. If saves stop
auto-refreshing the page, manually reload; if you want HMR fixed,
configure `server.hmr` to match your proxy URL.

## Build

```bash
npm run build
npm run preview
```

## How it works

1. Drag nodes from the left palette onto the canvas.
2. Connect nodes with `>>`-style edges. `Judge` exposes two source
   handles (`on_true` / `on_false`); pick the one you want to drag from.
3. Edit each node's parameters in the right panel. `Processor.fn`,
   `Judge.predicate(code)`, and each `Vote.model_list[*]` are written
   directly in Monaco — the function name in your `def` block is the
   one used in the generated file.
4. Export:
   - **pipeline.py** — runnable Python (single-direction codegen).
   - **.cdgraph.json** — full graph state (this is the source of truth;
     reload it later to keep editing).

`Vote` nodes do not connect on the canvas. They are referenced from a
`Judge` node's "predicate source = voteRef" dropdown and inlined into the
generated `Judge(Vote(...), ...)` call.

## Smoke test

The `scripts/smoke_codegen.ts` driver constructs a graph equivalent to
`examples/basic_pipeline.py` from the package, generates Python, and prints
it. Use `--write` to dump it to `scripts/pipeline.smoke.py`:

```bash
npx tsx scripts/smoke_codegen.ts --write
python -c "exec(open('scripts/pipeline.smoke.py').read())"   # builds Pipeline
```
