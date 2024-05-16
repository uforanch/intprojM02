"""
Keeps config validated to a standard, makes sure it exists.
"""

import os
import yaml
from pydantic import BaseModel
from typing import List

class Config(BaseModel):
    total_msgs : int = 1000
    senders: int = 3
    sender_rates: List[float] = [1.0]
    failure_rates: List[float] = [.2]
    frontend_refresh_time: float = .1
    producer_url: str = "http://localhost:8000"


CONFIG = None


def get_config():
    global CONFIG
    if not os.path.isfile("config.yaml"):
        with open("config.yaml", 'w') as f:
            CONFIG = Config()
            yaml.dump(CONFIG.dict(), f)
    else:
        with open("config.yaml", 'r') as f:
            CONFIG = Config.validate(yaml.safe_load(f))
    return CONFIG.dict()
"""
Additional functions were for unit test but did not work with producer.
Keeping them for manual testing.
"""
def save_config(config_dict):
    global CONFIG
    CONFIG = Config.validate(config_dict)
    with open("config.yaml", 'w') as f:
        yaml.dump(CONFIG.dict(), f)

def del_config():
    os.remove("config.yaml")