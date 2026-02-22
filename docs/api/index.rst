=============
API Reference
=============

This section collects generated reference documentation for the application's
core entry points.

.. grid:: 1 1 2 3
   :gutter: 2

   .. grid-item-card:: ASGI
      :link: asgi
      :link-type: doc

      Application entry points, lifecycle, and ASGI wiring.

   .. grid-item-card:: CLI
      :link: cli
      :link-type: doc

      Command-line interfaces for local and operational workflows.

   .. grid-item-card:: Utilities
      :link: utils
      :link-type: doc

      Cross-cutting utility modules used by the application.

.. note::

   The legacy module-level API trees under ``docs/api/domain`` and ``docs/api/lib``
   are being refreshed for the current code layout and are temporarily excluded
   from strict docs builds.

.. toctree::
    :titlesonly:
    :caption: Application API Reference
    :hidden:

    asgi
    cli
    utils
