# dataset.py
import os
import json
import configparser
from abc import ABC, abstractmethod
from typing import List, Dict


class IDatasetInterface(ABC):
    """
    ターゲットリスト(IPアドレス・ホスト名等)を読み込むデータセットの共通インターフェース。
    """
    def __init__(self):
        self.targets_list: List[Dict] = []
        self.load()

    @abstractmethod
    def load(self) -> None:
        """self.targets_list を構築する"""
        pass

    def __str__(self):
        return json.dumps(self.targets_list, indent=2, ensure_ascii=False)


class SwitchListDataset(IDatasetInterface):
    """
    config.ini
    CSV形式(1行目ヘッダー)からターゲットリストを読み込む。
    folder: settings, file: config.ini(実体はCSV)

    fetch ip address and hostname list from config life.
        - config.iniの内容を読み込んで、IPアドレスとホスト名のリストを作成する例。
        - config.iniは以下のような形式を想定（1行目がヘッダー、2行目以降がデータ）：
        ipaddr,hostname,username,password
    folder: settings
    file: config.ini
    """
    def __init__(self, settings_dir: str, config_file: str):
        self.targets_file = os.path.join(os.getcwd(), settings_dir, config_file)
        super().__init__()

    def load(self) -> None:
        with open(self.targets_file, 'r', encoding="utf-8") as f:
            headers = []
            for cnt, line in enumerate(f.readlines()):
                line = line.rstrip("\n")
                if not line:
                    continue
                items = line.split(",")
                if cnt == 0:
                    headers = items
                    continue
                device = {headers[idx]: (item if item != "" else None)
                          for idx, item in enumerate(items)}
                if device:
                    self.targets_list.append(device)


class ClusterIniDataset(IDatasetInterface):
    """
    configparser形式(cluster.ini)からクラスタのヘッドノード情報を読み込む。
    [cluster-a]
    ipaddr = 192.168.10.1
    hostname = cluster-a-headnode
    """
    def __init__(self, settings_dir: str, config_file: str):
        self.targets_file = os.path.join(os.getcwd(), settings_dir, config_file)
        super().__init__()

    def load(self) -> None:
        parser = configparser.ConfigParser()
        parser.read(self.targets_file, encoding="utf-8")
        for section in parser.sections():
            ipaddr = parser.get(section, "ipaddr", fallback=None)
            hostname = parser.get(section, "hostname", fallback=section)
            if not ipaddr and not hostname:
                continue
            self.targets_list.append({
                "ipaddr": ipaddr,
                "hostname": hostname,
            })