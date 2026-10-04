# Contributing

Issues and pull requests are welcome.

## Local development

1. Create a virtual environment.
2. Install `requirements-dev.txt`.
3. Run `pytest -q` before opening a pull request.
4. Keep provider-specific logic inside `app/providers.py` or a dedicated provider module.
5. Keep the UI vendor-neutral: provider brands should be options, not architectural requirements.

## Provider contributions

A provider should:

- fail clearly when credentials or dependencies are missing,
- avoid blocking the FastAPI event loop,
- document whether data leaves the user's machine,
- state when it depends on unofficial or undocumented endpoints,
- preserve existing OpenAI-compatible behavior.

## UI contributions

The WebUI should remain usable on an ordinary laptop without requiring a discrete GPU. Advanced local-model integrations are welcome as optional configurations.
