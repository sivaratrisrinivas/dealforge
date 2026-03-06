SOURCE: user-fal / SearchFal | https://docs.fal.ai/serverless/getting-started/core-concepts

# App

An App is a Python class that wraps your AI model for deployment. Your app defines what packages it needs, how to load your model, and how users interact with it.

```python
class MyApp(fal.App):
    machine_type = "GPU-H100"  # Choose your hardware

    def setup(self):
        # Load your model here
        # Executed on each runner

    @fal.endpoint("/")
    def generate(self, input_data):
        # Your endpoint logic here—usually a model call

    def teardown(self):
        # Cleanup code here
        # Executed on each runner when the runner is shutting down
```

**Endpoint**

An Endpoint is a function in your app that users can call via API. It defines how your model processes inputs and returns outputs.

---

# fal.App Reference

SOURCE: https://docs.fal.ai/reference/serverless-sdk/fal

Create a fal serverless application. Subclass this to define your application with custom setup, endpoints, and configuration. The App class handles model loading, request routing, and lifecycle management.

Example:

```python
class TextToImage(fal.App, machine_type="GPU"):
    requirements = ["diffusers", "torch"]

    def setup(self):
        self.pipe = StableDiffusionPipeline.from_pretrained(
            "runwayml/stable-diffusion-v1-5"
        )

    @fal.endpoint("/")
    def generate(self, prompt: str) -> dict:
        image = self.pipe(prompt).images[0]
        return {"url": fal.toolkit.upload_image(image)}
```

Class Variables (relevant): `requirements`, `machine_type`, `num_gpus`, `image` (ContainerImage), etc.
