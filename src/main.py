import os
import asyncio
from contextlib import asynccontextmanager
from typing import Annotated

import uvicorn
from fastapi.params import Depends

from src.models import Config
from src.mqtt import WiserMqtt
from src.wiser_client import WiserClient
from aiomqtt import Client
import logging
from fastapi import FastAPI

from src.wiser_state import CachedWiserClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


async def mqtt_main(config: Config, cached_wiser_client: CachedWiserClient):
    async with Client(config.mqtt_host, port=config.mqtt_port, username=config.mqtt_username,
                      password=config.mqtt_password) as client:
        mqtt = WiserMqtt(cached_wiser_client, client)

        while True:
            await mqtt.publish_data()
            await asyncio.sleep(60)


def load_config() -> Config:
    return Config(
        mqtt_host=os.environ["MQTT_HOST"],
        mqtt_port=int(os.environ["MQTT_PORT"]),
        mqtt_username=os.environ["MQTT_USERNAME"],
        mqtt_password=os.environ["MQTT_PASSWORD"],
        wiser_ip=os.environ["WISER_IP"],
        wiser_secret=os.environ["WISER_SECRET"],
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

    @app.get("/")
    async def read_root(cached_wiser: Annotated[CachedWiserClient, Depends(get_cached_wiser_client)]):
        info = await cached_wiser.get()
        return info.model_dump()

    return app


async def start_async():
    config = uvicorn.Config(create_fastapi(), host="0.0.0.0", port=8080, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == '__main__':
    asyncio.run(start_async())
