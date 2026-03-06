SOURCE: user-fal / SearchFal | https://docs.fal.ai/serverless/getting-started/core-concepts, https://docs.fal.ai/serverless/deployment-operations/machine-types, https://docs.fal.ai/serverless/distributed/overview

# Machine Type

Machine Type specifies the hardware (CPU or GPU) your app runs on. Choose based on your model's needs: "CPU" for lightweight models, "GPU-H100" for most AI models, or "GPU-B200" for large models.

## Configuration in App

```python
class MyApp(fal.App):
    machine_type = "GPU-H100"  # Choose your hardware
    num_gpus = 1
```

## GPU Machine Types

| Machine Type | RAM | VRAM | CPU Cores |
|--------------|-----|------|-----------|
| GPU-RTX4090 | 48 GB | 24 GB | 12 |
| GPU-RTX5090 | 60 GB | 32 GB | 30 |
| GPU-A100 | 60 GB | 40 GB | 12 |
| GPU-L40 | 100 GB | 48 GB | 6 |
| GPU-H100 | 112 GB | 80 GB | 12 |
| GPU-H200 | 112 GB | 141 GB | 12 |
| GPU-B200 | 210 GB | 192 GB | 19 |

## Multi-GPU (H100)

```python
class MyApp(fal.App):
    num_gpus = 8  # Request 8 GPUs
    machine_type = "GPU-H100"  # Each GPU will be an H100
```

Supported: GPU-H100 with num_gpus=2/4/8 : 2–8x H100 GPUs. GPU-A100 with num_gpus=2/4/8 : 2–8x A100 GPUs.

## Deploy CLI

```bash
fal deploy path/to/myapp.py::MyApp --machine-type GPU-A100 --num-gpus 1
```

## Fallback machine types

```python
class MyApp(fal.App):
    machine_type = ["GPU-A100-40GB", "GPU-A100-80GB"]
```
