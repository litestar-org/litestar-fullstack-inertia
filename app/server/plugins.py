from advanced_alchemy.extensions.litestar import SQLAlchemyPlugin
from litestar.plugins.flash import FlashConfig, FlashPlugin
from litestar.plugins.structlog import StructlogPlugin
from litestar_granian import GranianPlugin
from litestar_saq import SAQPlugin
from litestar_vite import VitePlugin
from litestar_vite.inertia import InertiaPlugin

from app import config
from app.server.core import ApplicationCore

structlog = StructlogPlugin(config=config.log)
vite = VitePlugin(config=config.vite)
saq = SAQPlugin(config=config.saq)
alchemy = SQLAlchemyPlugin(config=config.alchemy)
granian = GranianPlugin()
app_core = ApplicationCore()
flasher = FlashPlugin(config=FlashConfig(template_config=vite.template_config))
inertia = InertiaPlugin(config=config.inertia)
