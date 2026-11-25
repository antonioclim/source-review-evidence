# Optional offline Pyodide vendor directory

This is a placeholder for a separately prepared offline variant; Source Review Evidence does not bundle or qualify that runtime. A maintainer considering such a variant would place the authenticated Pyodide 0.25.0 `full/` files under:

```text
app/vendor/pyodide/v0.25.0/full/
```

The corresponding local-mode configuration retains production integrity. It is a configuration example, not evidence that the variant has passed the current dependency, server and browser checks:

```json
{
  "pyodide": {
    "mode": "local",
    "version": "0.25.0",
    "local_loader_url": "vendor/pyodide/v0.25.0/full/pyodide.js",
    "local_index_url": "vendor/pyodide/v0.25.0/full/",
    "provenance_url": "pyodide-provenance.json",
    "expected_loader_sha256": "9c79c9999999b15de7587aa220c61d06aa14e76babb75dc50c2f873aa826ad4d",
    "require_integrity": true,
    "verify_core_startup_set": true
  }
}
```

The browser verifies `pyodide.js`, `pyodide-lock.json`, `python_stdlib.zip`, `pyodide.asm.js` and `pyodide.asm.wasm` against `app/pyodide-provenance.json`. Do not replace those values with hashes calculated from an untrusted vendor copy. The local files must match the authenticated upstream bytes.

The provenance record covers the measured core startup set used by CodeProbe. It does not certify every optional package or the complete current vulnerability state. Follow [the separate offline-variant guide](../../../docs/05-offline-deployment.md), reconcile its dependency and serving boundary and preserve upstream notices. Current distribution integrity and actual browser execution require separate records; an earlier component gate is not a new release approval.
