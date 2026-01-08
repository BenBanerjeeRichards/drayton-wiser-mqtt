import os
import asyncio
import pathlib
from contextlib import asynccontextmanager
from typing import Annotated
from fastapi.middleware.cors import CORSMiddleware

import uvicorn
from fastapi.params import Depends
from starlette.responses import FileResponse
from starlette.staticfiles import StaticFiles

from src.models import Config, BoostHeatingRequest
from src.mqtt import WiserMqtt
from src.wiser_client import WiserClient
from aiomqtt import Client
import logging
from fastapi import FastAPI, HTTPException

from src.wiser_state import CachedWiserClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


async def mqtt_main(config: Config, cached_wiser_client: CachedWiserClient):
    try:
        async with Client(config.mqtt_host, port=config.mqtt_port, username=config.mqtt_username,
                          password=config.mqtt_password) as client:
            mqtt = WiserMqtt(config, cached_wiser_client, client)

            while True:
                await mqtt.publish_data()
                await asyncio.sleep(60)
    except Exception as e:
        # We want to quit the entire application if there is an unhandled error
        # Otherwise the task will stop without any other effect
        logging.exception("MQTT main loop failed")
        raise SystemExit(1) from e


def load_config() -> Config:
    return Config(
        mqtt_host=os.environ["MQTT_HOST"],
        mqtt_port=int(os.environ["MQTT_PORT"]),
        mqtt_username=os.environ["MQTT_USERNAME"],
        mqtt_password=os.environ["MQTT_PASSWORD"],
        wiser_ip=os.environ["WISER_IP"],
        wiser_secret=os.environ["WISER_SECRET"],
        disable_mqtt=os.environ.get("DISABLE_MQTT", "false").lower() == "true",
    )


def create_fastapi():
    config = load_config()
    wiser_client = WiserClient(config.wiser_ip, config.wiser_secret)
    cached_wiser_client = CachedWiserClient(wiser_client)

    async def get_cached_wiser_client():
        return cached_wiser_client

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        task = asyncio.create_task(mqtt_main(config, cached_wiser_client))

        yield
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            logging.info("Bridge task cancelled.")

    app = FastAPI(lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api")
    async def index(cached_wiser: Annotated[CachedWiserClient, Depends(get_cached_wiser_client)],
                    ignore_cache: bool = False):
        info = await cached_wiser.get(ignore_cache=ignore_cache)
        return info.model_dump()

    @app.patch("/api/heating/{room_id}/boost")
    async def boost_heating(boost_req: BoostHeatingRequest, room_id: int,
                            cached_wiser: Annotated[CachedWiserClient, Depends(get_cached_wiser_client)]):
        await cached_wiser.boost_heating(room_id, boost_req.temperature, boost_req.duration_minutes)
        info = await cached_wiser.get(ignore_cache=True)
        return info.model_dump()

    @app.patch("/api/heating/{room_id}/boost/cancel")
    async def cancel_heating_boost(room_id: int,
                                   cached_wiser: Annotated[CachedWiserClient, Depends(get_cached_wiser_client)]):
        await cached_wiser.cancel_heating_boost(room_id)
        info = await cached_wiser.get(ignore_cache=True)
        return info.model_dump()

    class SPAStaticFiles(StaticFiles):
        async def get_response(self, path: str, scope):
            try:
                return await super().get_response(path, scope)
            except (HTTPException, Exception):
                # If the file isn't found, serve the main index.html
                return FileResponse("../thermostat-fe/dist/index.html")

    BASE_DIR = pathlib.Path(__file__).parent.parent.resolve()
    DIST_DIR = BASE_DIR / "dist"
    app.mount("/", StaticFiles(directory=str(DIST_DIR), html=True), name="static")
    return app


async def start_async():
    config = uvicorn.Config(create_fastapi(), host="0.0.0.0", port=8080, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == '__main__':
    asyncio.run(start_async())
