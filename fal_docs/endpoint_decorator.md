SOURCE: user-fal / SearchFal | https://docs.fal.ai/serverless/getting-started/core-concepts, https://docs.fal.ai/reference/serverless-sdk/python

# @fal.endpoint(path)

Define an HTTP endpoint on an App.

## Usage

```python
from fal import App

class MyApp(fal.App):
    @fal.endpoint("/")
    def generate(self, input_data):
        # Your endpoint logic here
        return result

    @fal.endpoint("/custom-path")
    def custom(self, input: Input) -> Output:
        return Output(...)
```

## Key Decorators (Reference)

| Decorator | Description |
|-----------|-------------|
| @fal.endpoint(path) | Define an HTTP endpoint on an App |
| @fal.realtime(path) | WebSocket endpoint for realtime applications |
| @fal.function(...) | Create a standalone serverless function |
| @fal.cached | Cache function results in-memory |
