SOURCE: user-fal / SearchFal | https://docs.fal.ai/serverless/distributed/overview, https://docs.fal.ai/serverless/distributed/api-reference, https://docs.fal.ai/examples/serverless/deploy-multi-gpu-inference

# fal.distributed Overview

The fal.distributed module enables scaling AI workloads across multiple GPUs for inference and training. DistributedRunner orchestrates workers; DistributedWorker runs on each GPU.

## PyTorch Distributed Primitives

```python
import torch.distributed as dist

# Gather results from all GPUs to rank 0
dist.gather(tensor, gather_list if self.rank == 0 else None, dst=0)

# Broadcast data from rank 0 to all GPUs
dist.broadcast(tensor, src=0)

# Synchronize all GPUs at a barrier
dist.barrier()
```

## Example Usage

```python
from fal.distributed import DistributedRunner, DistributedWorker

class MyWorker(DistributedWorker):
    def setup(self, model_path):
        # Load model on this GPU (called once per worker)
        self.model = load_model(model_path).to(self.device)

    def __call__(self, prompt, **kwargs):
        # Process request (called for each request)
        return self.model.generate(prompt)

class MyApp(fal.App):
    num_gpus = 4  # Use 4 GPUs

    async def setup(self):
        # Create and start the runner
        self.runner = DistributedRunner(
            worker_cls=MyWorker,
            world_size=self.num_gpus
        )
        await self.runner.start(model_path="/data/model")

    @fal.endpoint("/")
    async def run(self, request: MyRequest):
        # Invoke workers for each request
        result = await self.runner.invoke({
            "prompt": request.prompt,
        })
        return result
```

## DistributedWorker Properties

- **self.device** — PyTorch CUDA device for this worker (cuda:0, cuda:1, etc.). Use `.to(self.device)` when loading models.
- **self.rank** — Worker ID (0 to world_size-1). Rank 0 is typically the main worker that returns results.
- **self.world_size** — Total number of workers (GPUs).

## DistributedRunner Constructor

```python
from fal.distributed import DistributedRunner, DistributedWorker

class MyWorker(DistributedWorker):
    def setup(self, **kwargs):
        self.model = load_model().to(self.device)

    def __call__(self, prompt: str, **kwargs):
        return self.model.generate(prompt)

# Create runner for 4 GPUs
runner = DistributedRunner(
    worker_cls=MyWorker,
    world_size=4,
)
```

Parameters:
- **worker_cls** (type[DistributedWorker]): Your custom worker class that inherits from DistributedWorker.
- **world_size** (int): Total number of worker processes to spawn (typically equals num_gpus).

## DistributedWorker device property

Returns the CUDA device assigned to this worker. Returns: `torch.device` (e.g., cuda:0, cuda:1).

```python
class MyWorker(DistributedWorker):
    def setup(self):
        # Load model on this worker's GPU
        self.model = MyModel().to(self.device)
        print(f"Model loaded on {self.device}")
```

## DDP Training Example (dist.broadcast_object_list, gather)

```python
class DDPWorker(DistributedWorker):
    def setup(self, **kwargs):
        from torch.nn.parallel import DistributedDataParallel as DDP

        self.model = MyModel().to(self.device)
        self.model = DDP(self.model, device_ids=[self.rank], output_device=self.rank)
        self.optimizer = torch.optim.Adam(self.model.parameters())

    def __call__(self, data_path: str, **kwargs):
        import torch.distributed as dist

        if self.rank == 0:
            data = load_data(data_path)
        else:
            data = None

        data = dist.broadcast_object_list([data], src=0)[0]
        local_batch = data[self.rank::self.world_size]
        # ... training loop ...
```

## Streaming with gather (add_streaming_result)

```python
from fal.distributed import DistributedWorker
import torch.distributed as dist

class MultiGPUStreamingWorker(DistributedWorker):
    def __call__(self, prompt: str, num_steps: int = 20):
        for step in range(0, num_steps, 5):
            intermediate = self.model.step(prompt)

            if self.rank == 0:
                gather_list = [
                    torch.zeros_like(intermediate, device=self.device)
                    for _ in range(self.world_size)
                ]
            else:
                gather_list = None

            dist.gather(intermediate, gather_list, dst=0)

            if self.rank == 0:
                combined = self.combine_results(gather_list)
                self.add_streaming_result({
                    "step": step,
                    "preview": combined,
                    "num_gpus": self.world_size,
                }, as_text_event=True)

            dist.barrier()
        return {"final": final_result}
```

## SDK Reference (fal.distributed)

SOURCE: https://docs.fal.ai/reference/serverless-sdk/fal.distributed

```python
from fal.distributed import DistributedRunner, DistributedWorker
```

DistributedWorker: rank, world_size, device, queue, loop, thread, running.
DistributedRunner: worker_cls, world_size, master_addr, master_port, worker_addr, worker_port, timeout, etc.
