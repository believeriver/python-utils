# test/conftest.py
import sys
import os
import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from executor import ServerInfo
from config import Config


@pytest.fixture
def sample_one_target() -> list:
    return [
        {"ipaddr": "192.168.64.2", "hostname": "rx8headnode",
         "username": Config.USERNAME, "password": Config.PASSWORD},
    ]


@pytest.fixture
def sample_datasets() -> list:
    return [
        {"ipaddr": "192.168.64.2", "hostname": "rx8headnode"},
        {"ipaddr": "192.168.64.4", "hostname": "rx8node01",
         "username": Config.USERNAME, "password": Config.PASSWORD},
        {"ipaddr": "192.168.64.2", "hostname": "rx8headnode",
         "username": Config.USERNAME, "password": Config.PASSWORD},
        {"ipaddr": None, "hostname": None},
    ]