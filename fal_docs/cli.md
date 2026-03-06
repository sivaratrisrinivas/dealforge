# Fal CLI: run and deploy

SOURCE: https://docs.fal.ai/serverless/getting-started/core-concepts, https://docs.fal.ai/reference/cli/run, https://docs.fal.ai/reference/cli/deploy

## fal run (development / ephemeral)

Test your app on a single cloud GPU. Creates a temporary URL that disappears when you stop the command. Defaults to **public** auth.

```bash
fal run path/to/myfile.py::MyApp
fal run path/to/myfile.py::MyApp --auth private
fal run path/to/myfile.py::MyApp --env staging
```

- **--auth public** (default): Anyone can call without authentication; you pay for usage.
- **--auth private**: Only you or your team can call; requires API key.

## fal deploy (production / persistent)

Deploy your app to production. Creates a permanent URL. Defaults to **private** auth (API key required).

```bash
fal deploy path/to/myfile.py::MyApp
fal deploy path/to/myfile.py::MyApp --app-name myapp --auth private
fal deploy path/to/myfile.py::MyApp --auth private --env main
```

Positional: `app_ref` = file path or `path/to/file.py::ClassName`.
Options: `--auth` (private | public), `--app-name`, `--team`, `--env`, `--strategy`, etc.

## Quick reference

- **Run (test)**: `fal run app.py::MyApp --auth private`
- **Deploy (production)**: `fal deploy app.py::MyApp --auth private`
