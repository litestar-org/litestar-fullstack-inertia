from advanced_alchemy.extensions.litestar import SQLAlchemyPlugin
from litestar.plugins.flash import FlashConfig, FlashPlugin
from litestar.plugins.structlog import StructlogPlugin
from litestar_granian import GranianPlugin
from litestar_vite import VitePlugin

from app import config
from app.server.core import ApplicationCore

structlog = StructlogPlugin(config=config.log)
vite = VitePlugin(config=config.vite)
alchemy = SQLAlchemyPlugin(config=config.alchemy)
granian = GranianPlugin()
app_core = ApplicationCore()
# FlashPlugin requires template_config even though Inertia handles flash via props
flasher = FlashPlugin(config=FlashConfig(template_config=config.templates))
