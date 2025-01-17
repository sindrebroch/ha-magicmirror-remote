"""MagicMirror API."""

from http import HTTPStatus
from typing import Any

import aiohttp

from custom_components.magicmirror.const import LOGGER
from custom_components.magicmirror.models import (
    GenericResponse,
    ModuleResponse,
    ModuleUpdateResponses,
    MonitorResponse,
    QueryResponse,
)

# Mirror control
API_TEST = "api/test"
API_MONITOR = "api/monitor"
API_MONITOR_ON = f"{API_MONITOR}/on"
API_MONITOR_OFF = f"{API_MONITOR}/off"
API_MONITOR_STATUS = f"{API_MONITOR}/status"
API_MONITOR_TOGGLE = f"{API_MONITOR}/toggle"

API_SHUTDOWN = "api/shutdown"
API_REBOOT = "api/reboot"
API_RESTART = "api/restart"
API_MINIMIZE = "api/minimize"
API_TOGGLEFULLSCREEN = "api/togglefullscreen"
API_DEVTOOLS = "api/devtools"
API_REFRESH = "api/refresh"
API_BRIGHTNESS = "api/brightness"

# Module control
API_MODULE = "api/module"
API_MODULES = "api/modules"
API_MODULE_INSTALLED = f"{API_MODULE}/installed"
API_MODULE_AVAILABLE = f"{API_MODULE}/available"
API_UPDATE_MODULE = "api/update"
API_INSTALL_MODULE = "api/install"
API_MM_UPDATE_AVAILABLE = "api/mmUpdateAvailable"
API_UPDATE_AVAILABLE = "api/updateAvailable"

# API
API_CONFIG = "api/config"

SWAGGER = "/api/docs/#/"


class MagicMirrorApiClient:
    """Main class for handling connection with."""

    def __init__(
        self,
        host: str,
        port: str,
        api_key: str,
        session: aiohttp.client.ClientSession | None = None,
    ) -> None:
        """Initialize connection with MagicMirror."""
        self.host = host
        self.port = port
        self.api_key = api_key
        self._session = session

        self.base_url = f"http://{self.host}:{self.port}"
        self.headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

    async def handle_request(self, response) -> Any:
        """Handle request."""
        LOGGER.debug("pre handle_request=%s", response)

        async with response as resp:
            if resp.status == HTTPStatus.FORBIDDEN:
                exception = f"Forbidden {resp}. Check for missing API-key."
                raise Exception(exception)

            if resp.status != HTTPStatus.OK:
                LOGGER.warning("Response not 200 OK %s", resp)
                data = None
            else:
                data = await resp.json()
                LOGGER.debug("post handle_request=%s", data)

        return data

    async def get(self, path: str) -> Any:
        """Get request."""
        get_url = f"{self.base_url}/{path}"
        LOGGER.debug("GET url=%s. headers=%s", get_url, self.headers)

        if self._session is None:
            LOGGER.warning("There is no session")
            return None

        get = await self._session.get(
            url=get_url,
            headers=self.headers,
        )

        LOGGER.debug("Response=%s", get)

        return await self.handle_request(get)

    async def system_call(self, path: str) -> None:
        """Get request."""
        get_url = f"{self.base_url}/{path}"
        LOGGER.debug("GET url=%s. headers=%s", get_url, self.headers)

        if self._session is None:
            LOGGER.warning("There is no session")
            return

        try:
            await self._session.get(
                url=get_url,
                headers=self.headers,
            )
        except (aiohttp.ClientConnectionError, aiohttp.ServerDisconnectedError) as e:
            LOGGER.error(
                "Connection error: %s. Check if the MagicMirror service is running.", e
            )

    async def post(self, path: str, data: str | None = None) -> Any:
        """Post request."""
        post_url = f"{self.base_url}/{path}"
        LOGGER.debug("POST url=%s. data=%s. headers=%s", post_url, data, self.headers)

        if self._session is None:
            LOGGER.warning("There is no session")
            return None

        post = (
            await self._session.post(
                url=post_url,
                headers=self.headers,
                data=data,
            ),
        )

        LOGGER.debug("Response=%s", post)

        return await self.handle_request(post)

    async def api_test(self) -> GenericResponse:
        """Test api."""
        return GenericResponse.from_dict(await self.get(API_TEST))

    async def mm_update_available(self) -> QueryResponse:
        """Get update available status."""
        return QueryResponse.from_dict(await self.get(API_MM_UPDATE_AVAILABLE))

    async def update_available(self) -> ModuleUpdateResponses:
        """Get update available status."""
        response = await self.get(API_UPDATE_AVAILABLE)
        if response is None:
            return ModuleUpdateResponses(success=False, result=[])
        return ModuleUpdateResponses.from_dict(response)

    async def monitor_status(self) -> MonitorResponse:
        """Get monitor status."""
        return MonitorResponse.from_dict(await self.get(API_MONITOR_STATUS))

    async def get_modules(self) -> ModuleResponse:
        """Get module status."""
        return ModuleResponse.from_dict(await self.get(API_MODULE))

    async def monitor_on(self) -> Any:
        """Turn on monitor."""
        return MonitorResponse.from_dict(await self.get(API_MONITOR_ON))

    async def monitor_off(self) -> Any:
        """Turn off monitor."""
        return MonitorResponse.from_dict(await self.get(API_MONITOR_OFF))

    async def monitor_toggle(self) -> Any:
        """Toggle monitor."""
        return MonitorResponse.from_dict(await self.get(API_MONITOR_TOGGLE))

    async def shutdown(self) -> None:
        """Shutdown."""
        await self.system_call(API_SHUTDOWN)

    async def reboot(self) -> None:
        """Reboot."""
        await self.system_call(API_REBOOT)

    async def restart(self) -> None:
        """Restart."""
        await self.system_call(API_RESTART)

    async def refresh(self) -> None:
        """Refresh."""
        await self.system_call(API_REFRESH)

    async def minimize(self) -> Any:
        """Minimize."""
        return await self.get(API_MINIMIZE)

    async def toggle_fullscreen(self) -> Any:
        """Toggle fullscreen."""
        return await self.get(API_TOGGLEFULLSCREEN)

    async def devtools(self) -> Any:
        """Devtools."""
        return await self.get(API_DEVTOOLS)

    async def brightness(self, brightness: str) -> Any:
        """Brightness."""
        return await self.get(f"{API_BRIGHTNESS}/{brightness}")

    async def get_brightness(self) -> QueryResponse:
        """Brightness."""
        return QueryResponse.from_dict(await self.get(API_BRIGHTNESS))

    async def module(self, module_name: str) -> Any:
        """Endpoint for module."""
        return await self.get(f"{API_MODULE}/{module_name}")

    async def module_action(self, module_name: str, action) -> Any:
        """Endpoint for module action."""
        return await self.get(f"{API_MODULE}/{module_name}/{action}")

    async def module_update(self, module_name: str) -> Any:
        """Endpoint for module update."""
        return await self.get(f"{API_UPDATE_MODULE}/{module_name}")

    async def modules(self) -> Any:
        """Endpoint for modules."""
        return await self.get(API_MODULES)

    async def module_installed(self) -> Any:
        """Endpoint for module installed."""
        return await self.get(API_MODULE_INSTALLED)

    async def module_available(self) -> Any:
        """Endpoint for module available."""
        return await self.get(API_MODULE_AVAILABLE)

    async def module_install(self, data) -> Any:
        """Endpoint for module install."""
        return await self.post(API_INSTALL_MODULE, data=data)

    async def config(self) -> Any:
        """Config."""
        return await self.get(API_CONFIG)

    async def show_module(self, module) -> Any:
        """Show module."""
        return await self.get(f"{API_MODULE}/{module}/show")

    async def hide_module(self, module) -> Any:
        """Hide module."""
        return await self.get(f"{API_MODULE}/{module}/hide")

    async def alert(
        self,
        title: str,
        msg: str,
        timer: str,
        dropdown: bool = False,
    ) -> Any:
        """Notification screen."""
        alert = "&type=notification" if dropdown else ""

        return await self.get(
            f"{API_MODULE}/alert/showalert?title={title}&message={msg}&timer={timer}{alert}"
        )
