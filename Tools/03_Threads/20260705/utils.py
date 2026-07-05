import os
import json
from abc import ABC, abstractmethod
from typing import List
from pprint import pformat

from config import Config

# -----------------------------------
# Fetch Target List from config file
# -----------------------------------
class SwitchListDataset(object):
    """
    fetch ip address and hostname list from config life.
        - config.iniの内容を読み込んで、IPアドレスとホスト名のリストを作成する例。
        - config.iniは以下のような形式を想定（1行目がヘッダー、2行目以降がデータ）：
        ipaddr,hostname,username,password
    folder: settings
    file: config.ini
    """
    def __init__(self, _targets_file=None):
        cur_dir = os.getcwd()
        if _targets_file is not None:
            self.targets_file = _targets_file
        else:
            self.targets_file = os.path.join(cur_dir, Config.SETTINGS_DIR, Config.CONFIG_FILE)
        self.targets_list = []
        self.import_config()

    def import_config(self):
        with open(self.targets_file, 'r', encoding="utf-8") as f:
            headers = []
            lines = f.readlines()
            for cnt, line in enumerate(lines):
                device = {}
                line = line.rstrip("\n")
                items = line.split(",")
                if cnt == 0:
                    for item in items:
                        headers.append(item)
                else:
                    for idx, item in enumerate(items):
                        if item == "":
                            item = None
                        device[headers[idx]] = item
                if not line:
                    continue
                if device != {}:
                    self.targets_list.append(device)

    def __str__(self):
        return json.dumps(self.targets_list, indent=2, ensure_ascii=False)


