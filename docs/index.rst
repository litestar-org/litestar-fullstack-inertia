==================
Litestar Fullstack
==================

Litestar Fullstack Inertia is a production-ready reference application that combines
`Litestar <https://litestar.dev>`_, `React 19 <https://react.dev/>`_,
`Inertia.js <https://inertiajs.com/>`_, and `Vite <https://vitejs.dev/>`_ to build modern
server-driven web applications.

Use it as a complete starting point for new projects or as a reference implementation for
auth flows, project architecture, and operational workflows.

Highlights
----------

- Inertia.js frontend delivery with React and TypeScript
- Litestar backend with authentication, team-based access, and CLI tooling
- SQLAlchemy + Alembic database workflow with production-oriented defaults
- Dockerized development setup and test automation

.. grid:: 1 1 2 2
   :gutter: 2

   .. grid-item-card:: Install the Project
      :link: usage/installation
      :link-type: doc

      Set up dependencies, local services, and the development environment.

   .. grid-item-card:: Usage Guide
      :link: usage/index
      :link-type: doc

      Follow the development and startup workflows for day-to-day work.

   .. grid-item-card:: API Reference
      :link: api/index
      :link-type: doc

      Browse generated API docs for core modules, domains, and shared libraries.

   .. grid-item-card:: Contributing
      :link: contribution-guide
      :link-type: doc

      Review contribution guidelines, quality checks, and pull request workflow.

.. grid:: 1
   :gutter: 2

   .. grid-item-card:: Changelog
      :link: changelog
      :link-type: doc

      Track notable updates and release history.

.. toctree::
    :titlesonly:
    :caption: Documentation
    :hidden:

    usage/index
    api/index

.. toctree::
    :titlesonly:
    :caption: Development
    :hidden:

    contribution-guide
    changelog
