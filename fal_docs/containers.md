SOURCE: user-fal / SearchFal | https://docs.fal.ai/examples/serverless/deploy-models-with-custom-containers, https://docs.fal.ai/serverless/development/use-custom-container-image, https://docs.fal.ai/reference/serverless-sdk/fal

# ContainerImage.from_dockerfile_str()

## Full Example

```python
import fal
from fal.container import ContainerImage

dockerfile_str = """
FROM python:3.11

RUN apt-get update && apt-get install -y ffmpeg
RUN pip install pyjokes ffmpeg-python
"""

custom_image = ContainerImage.from_dockerfile_str(
    dockerfile_str,
    registries={
        "https://my.registry.io/": {
            "username": <username>,
            "password": <password>,
        },
    },
)

class Test(fal.App):
    image = custom_image
    machine_type = "GPU"

    requirements = ["torch"]

    def setup(self):
        import subprocess
        subprocess.run(["nvidia-smi"])

    @fal.endpoint("/")
    def index(self):
        return "Hello, World!"
```

## Alternative: from_dockerfile (path)

```python
from fal.container import ContainerImage
from pathlib import Path

PWD = Path(__file__).resolve().parent

class MyApp(fal.App):
    image = ContainerImage.from_dockerfile(f"{PWD}/Dockerfile")

    def setup(self):
        ...

    @fal.endpoint("/")
    def predict(self, input: Input) -> Output:
        # Rest is your imagination.
```

## API Reference

SOURCE: https://docs.fal.ai/reference/serverless-sdk/fal

```python
from fal.container import ContainerImage

# Class method
def from_dockerfile_str(cls, text: str, **kwargs) -> ContainerImage
```

Parameters: `text` (str), `**kwargs` (build_args, registries, builder, etc.).
