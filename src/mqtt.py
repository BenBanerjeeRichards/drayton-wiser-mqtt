from aiomqtt import Client

import logging

from src.models import Config
from src.wiser_state import CachedWiserClient
import json

class WiserMqtt:

    def __init__(self, config: Config, wiser_state: CachedWiserClient, mqtt_client: Client):
        self.wiser_api = wiser_state
        self.mqtt_client = mqtt_client
        self.config = config

    async def publish_data(self):
        logging.info("Publishing wiser stats to MQTT")
        # Always get latest state for mqtt, but use cached api to put items in cache for other calls
        state = await self.wiser_api.get(ignore_cache=True)
        if self.config.disable_mqtt:
            logging.info("MQTT disabled, not publishing data")
            return

        for stat in state.room_stats:
            await self.mqtt_client.publish(f"wiser/room_stats/{stat.id}", json.dumps({
                "temperature": stat.temperature,
                "humidity": stat.humidity,
            }))

        for heating in state.heating_channels:
            await self.mqtt_client.publish(f"wiser/heating_channel/{heating.id}", json.dumps({
                "demand_percent": heating.demand_percent,
            }))

        for hot_water in state.hot_water_channels:
            await self.mqtt_client.publish(f"wiser/hot_water_channel/{hot_water.id}", json.dumps({
                "is_firing": hot_water.is_firing,
            }))

        for room in state.rooms:
            await self.mqtt_client.publish(f"wiser/room/{room.id}", json.dumps({
                "demand_percent": room.demand_percent,
                "current_temperature": room.current_temperature,
                "setpoint_temperature": room.setpoint_temperature,
                "control_source": room.control_source,
                "is_firing": room.is_firing,
            }))
