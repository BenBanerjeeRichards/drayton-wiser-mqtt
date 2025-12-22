import asyncio
import os
import asyncio

from src.models import Config
from src.wiser_client import WiserApi, WiserClient
from aiomqtt import Client

async def async_main():
    config = load_config()
    wiser_client =  WiserClient(config.wiser_ip, config.wiser_secret)
    wiser_client.get_state()
    async with Client(config.mqtt_host, port=config.mqtt_port, username=config.mqtt_username,
                      password=config.mqtt_password) as client:
        print("Connected")

    # client.boost_hot_water(2, 60)


def load_config() -> Config:
    return Config(
        mqtt_host=os.environ["MQTT_HOST"],
        mqtt_port=int(os.environ["MQTT_PORT"]),
        mqtt_username=os.environ["MQTT_USERNAME"],
        mqtt_password=os.environ["MQTT_PASSWORD"],
        wiser_ip=os.environ["WISER_IP"],
        wiser_secret=os.environ["WISER_SECRET"],
    )

if __name__ == '__main__':
    asyncio.run(async_main())
