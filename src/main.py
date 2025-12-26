import os
import asyncio
import json
from src.models import Config
from src.wiser_client import WiserClient
from aiomqtt import Client
import logging


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

async def async_main():
    config = load_config()
    wiser_client =  WiserClient(config.wiser_ip, config.wiser_secret)

    async with Client(config.mqtt_host, port=config.mqtt_port, username=config.mqtt_username,
                      password=config.mqtt_password) as client:
        # proof of concept
        while True:
            logging.info("Publishing wiser stats to MQTT")
            state = wiser_client.get_state()
            print(state.room_stats[0])

            for stat in state.room_stats:
                await client.publish(f"wiser/room_stats/{stat.id}", json.dumps({
                    "temperature": stat.temperature,
                    "humidity": stat.humidity,
                }))

            for heating in state.heating_channels:
                await client.publish(f"wiser/heating_channel/{heating.id}", json.dumps({
                    "demand_percent": heating.demand_percent,
                }))

            for hot_water in state.hot_water_channels:
                await client.publish(f"wiser/hot_water_channel/{hot_water.id}", json.dumps({
                    "is_firing": hot_water.is_firing,
                }))

            for room in state.rooms:
                await client.publish(f"wiser/room/{room.id}", json.dumps({
                    "demand_percent": room.demand_percent,
                    "current_temperature": room.current_temperature,
                    "setpoint_temperature": room.setpoint_temperature,
                    "control_source": room.control_source,
                }))

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

if __name__ == '__main__':
    asyncio.run(async_main())
