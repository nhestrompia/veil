# Shared pixel-buffer calibration

Default allocations did not allow the tested cross-process lookup by numeric identifier. Explicit global allocations did allow exact fake-byte recovery. This result covers cooperating fake buffers on macOS 26.6. It does not establish browser capture protection.

The producer holds each unchanged 16 by 16 BGRA buffer until the reader finishes. The reader receives only that buffer's identifier. It receives no expected bytes, surface object, or Mach port. The controller compares the recovered value with a fresh random value.

| Allocation | Default readable | Explicit false readable | Explicit true readable |
| --- | --- | --- | --- |
| Direct IOSurface | 0/3 | 0/3 | 3/3 |
| Core Video pixel buffer | 0/3 | 0/3 | 3/3 |

The six global controls recovered the exact value. All twelve default or explicit-false lookups returned nil. A failed lookup describes this tested route. It does not establish confidentiality for every browser buffer or every access method.

The global property is deprecated. The build preserves that warning because the property itself is the positive control. The browser's allocation policy remains unchanged. The reader never enumerates identifiers or reads another application's pixels.

The [saved results](evidence/surface-results.json) include the binary hash and each lookup result. The [primary-source research](research/iosurface-boundary.md) separates numeric identifiers from Mach-port transfer. The tests do not compare lookup before and after display-layer enqueue. They do not supply an identifier-discovery attack against the browser.

```sh
bash scripts/build-surface-probe.sh
python3 tools/run_surface_probe.py --repetitions 3 --output artifacts/surface-calibration
```
