===================
Starting the server
===================

This section describes how to start the server in development and production modes.

Development
^^^^^^^^^^^

In development mode, the Litestar application automatically manages the Vite development server.

When ``VITE_DEV_MODE`` is ``True`` (default in ``.env.local.example``):
1. The **Granian** ASGI server starts the Python application.
2. The **litestar-vite** plugin launches the **Vite** dev server in a subprocess.
3. HMR (Hot Module Replacement) is enabled for instant frontend updates.

.. dropdown:: Starting the server in dev mode

  .. code-block:: bash

      (.venv) user@local:~/Code/litestar-fullstack-inertia$ uv run app run --reload
      Using Litestar app from env: 'app.server.asgi:create_app'
      Loading environment configuration from .env
      Starting Granian server process...
      Starting Vite process with HMR Enabled...

      > dev
      > vite

      [INFO] Listening at: http://0.0.0.0:8000

      ➜  Local:   http://localhost:5173/
      ➜  APP_URL: http://localhost:8000

Production
^^^^^^^^^^

In production, frontend assets must be built beforehand. The server will serve these static files directly.

1. **Build Assets**: Compiles TypeScript/React to static JS/CSS.
2. **Run Server**: Starts Granian without the Vite subprocess.

.. code-block:: bash
  :caption: Build assets for production

    make build
    # OR manually:
    uv run app assets build

.. dropdown:: Starting the server in production mode

  .. code-block:: bash

      (.venv) user@local:~/Code/litestar-fullstack-inertia$ uv run app run
      Using Litestar app from env: 'app.server.asgi:create_app'
      Loading environment configuration from .env
      ...
      Serving assets using manifest at `.../public/manifest.json`.
      [INFO] Listening at: http://0.0.0.0:8000
