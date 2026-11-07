# Model Speed & X-Velocity Benchmark

Generated: 2026-11-07T23:41:48.904554Z
Machine: macOS-26.6.1-x86_64-i386-64bit-Mach-O | Python 3.14.7 | i386

## Method
- X-velocity sweep: 1000x upward (x2) until throughput/time cap.
- Measures local dispatch/registry/routing/pricing/provision ops (credential-safe; no external API calls).
- LLM token-generation speed is backend-dependent (llama.cpp/ctransformers/remote provider) and measured separately when a model is loaded.

## Result
- Limit reached: **True**
- Peak avg ops/sec (local dispatch): **856,576.94**

## Scale Table
| X | Avg ops/sec | Sample ops | Notes |
|---:|---:|---|---|
| 1000 | 590,762.77 | registry_list_models=27,926/s, registry_status=30,935/s, mesh_pool_status=143,936/s | ok |
| 2000 | 658,102.68 | registry_list_models=13,297/s, registry_status=26,838/s, mesh_pool_status=162,588/s | ok |
| 4000 | 547,056.35 | registry_list_models=36,745/s, registry_status=18,593/s, mesh_pool_status=61,237/s | ok |
| 8000 | 856,576.94 | registry_list_models=31,282/s, registry_status=22,002/s, mesh_pool_status=198,070/s | Reached throughput/time cap around 8000x on this machine (time budget 1.0s/scale/op). |

## Per-Provider Speed Assessment
| Provider | Category | Configured | Models | Real >=1MB | Inference path | Assessment |
|---|---|:---:|---:|---:|---|---|
| QB Protocol Local Models | local_gguf | yes | 1 | 1 | local_cpu_bound (ctransformers/llama.cpp when loaded); dispatch near measured peak | dispatch ~856576 ops/s; token gen measured separately via loaded backend |
| GNU 3.4 AlienWare Models | local_gguf | yes | 22 | 0 | local_cpu_bound (ctransformers/llama.cpp when loaded); dispatch near measured peak | dispatch ~856576 ops/s; token gen measured separately via loaded backend |
| OpenAI / ChatGPT | openai | no | 3 | 0 | remote API (network+provider-bound); credentials required via env vars | local dispatch ~856576 ops/s; inference latency dominated by provider/network |
| Anthropic Claude | anthropic | no | 3 | 0 | remote API (network+provider-bound); credentials required via env vars | local dispatch ~856576 ops/s; inference latency dominated by provider/network |
| NVIDIA Nemotron | nemotron | no | 2 | 0 | remote API (network+provider-bound); credentials required via env vars | local dispatch ~856576 ops/s; inference latency dominated by provider/network |
| HuggingFace Hub | huggingface | yes | 0 | 0 | remote API (network+provider-bound); credentials required via env vars | local dispatch ~856576 ops/s; inference latency dominated by provider/network |
| Argon-VC Vercel Portal | vercel | no | 0 | 0 | bridge/portal dispatch (network-bound when remote tunnel used) | local dispatch ~856576 ops/s; end-to-end adds tunnel+portal latency |

## Dataset Footprint (this machine)
| Location | GGUF total | >=1MB | Total size |
|---|---:|---:|---:|
| `/Users/jjmarte/delta-stream/qb_protocol/models` | 1 | 1 | 637.81 MB |
| `/Users/jjmarte/speed/Gnu-3.4-console-edition/alien ware/gnu 3.4` | 22 | 0 | 0.19 MB |

Unified registry: **7 providers / 31 model entries**. Categories: `{'local_gguf': 2, 'openai': 1, 'anthropic': 1, 'nemotron': 1, 'huggingface': 1, 'vercel': 1}`.

## Notes
- Measures local dispatch/registry/routing/pricing/provision throughput (no credentials, no external model API calls).
- Actual LLM token generation speed depends on backend load, model size, and whether llama.cpp/ctransformers/remote API is used.
- GNU 3.4 entries are discovered; files <1MB are stubs and not benchmarked for inference.

Raw JSON: `~/.qb_protocol_velocity_benchmark.json`. Run `POST /benchmark/velocity` or `GET /benchmark/velocity` to refresh.
