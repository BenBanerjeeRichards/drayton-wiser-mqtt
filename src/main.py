import os
import asyncio
import pathlib
from contextlib import asynccontextmanager, AsyncExitStack
from typing import Annotated
from fastapi.middleware.cors import CORSMiddleware

import uvicorn
from fastapi.params import Depends
from starlette.responses import FileResponse

from src.models import Config, BoostHeatingRequest, BoostHotWaterRequest
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
        async with AsyncExitStack() as stack:
            mqtt_client = None
            if config.mqtt_host and not config.disable_mqtt:
                mqtt_client = await stack.enter_async_context(
                    Client(config.mqtt_host, port=config.mqtt_port, username=config.mqtt_username,
                           password=config.mqtt_password))

            mqtt = None if not mqtt_client else WiserMqtt(cached_wiser_client, mqtt_client)

            while True:
                state = await cached_wiser_client.get(ignore_cache=True)
                if mqtt:
                    await mqtt.publish_data(state)
                else:
                    logging.info("MQTT not configured or disabled, skipping publishing")
                await asyncio.sleep(60)
    except Exception as e:
        # We want to quit the entire application if there is an unhandled error
        # Otherwise the task will stop without any other effect
        logging.exception("MQTT main loop failed")
        raise SystemExit(1) from e


def load_config() -> Config:
    has_mqtt = os.environ.get("MQTT_HOST")
    if has_mqtt:
        assert "MQTT_PORT" in os.environ
        assert "MQTT_USERNAME" in os.environ
        assert "MQTT_PASSWORD" in os.environ

    return Config(
        mqtt_host=os.environ.get("MQTT_HOST"),
        mqtt_port=None if not has_mqtt else int(os.environ["MQTT_PORT"]),
        mqtt_username=os.environ.get("MQTT_USERNAME"),
        mqtt_password=os.environ.get("MQTT_PASSWORD"),
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

    @app.patch("/api/hot_water/{channel_id}/boost")
    async def boost_hot_water(boost_req: BoostHotWaterRequest, channel_id: int,
                              cached_wiser: Annotated[CachedWiserClient, Depends(get_cached_wiser_client)]):
        await cached_wiser.boost_hot_water(channel_id, boost_req.duration_minutes)
        info = await cached_wiser.get(ignore_cache=True)
        return info.model_dump()

    @app.patch("/api/hot_water/{channel_id}/boost/cancel")
    async def cancel_hot_water_boost(channel_id: int,
                                     cached_wiser: Annotated[CachedWiserClient, Depends(get_cached_wiser_client)]):
        await cached_wiser.cancel_hot_water(channel_id)
        info = await cached_wiser.get(ignore_cache=True)
        return info.model_dump()

    # Serve react application from here
    # In the future we should really split this up to allow separate deployments
    BASE_DIR = pathlib.Path(__file__).parent.parent.resolve()
    DIST_DIR = BASE_DIR / "dist"

    # app.mount("/", StaticFiles(directory=str(DIST_DIR), html=True), name="static")

    @app.get("/{path:path}")
    async def serve_spa(path: str):
        # Build the actual path to the file
        file_path = os.path.join(DIST_DIR, path)

        # If the requested path is a real file (css, js, images), serve it
        if os.path.isfile(file_path):
            return FileResponse(file_path)

        # Otherwise, serve index.html so React Router can take over
        return FileResponse(os.path.join(DIST_DIR, "index.html"))

    return app


async def start_async():
    config = uvicorn.Config(create_fastapi(), host="0.0.0.0", port=8080, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == '__main__':
    asyncio.run(start_async())
