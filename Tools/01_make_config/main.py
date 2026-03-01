import sys
import os
import logging
from datetime import datetime
from typing import List
import gc

logging.basicConfig(
        stream=sys.stdout,
        level=logging.INFO,
        format='%(asctime)s:%(name)s:%(levelname)s:%(message)s')
logger = logging.getLogger(__name__)


class CreateConfig(object):
    def __init__(self, _template_file: str, _devices_file: str, _out_dir: str):
        self.template_file = _template_file
        self.devices_file = _devices_file
        self.out_dir = _out_dir
        self.template_config = []
        self.created_config = []
        self.devices_list = []

    def import_template(self):
        with open(self.template_file, 'r', encoding="utf-8") as f:
            for line in f:
                line = line.rstrip("\n")
                if not line:
                    continue
                # print(line)
                self.template_config.append(line)

    def import_input_list(self):
        with open(self.devices_file, 'r', encoding="utf-8") as f:
            # header = f.readline().strip().split(",")
            headers = []

            lines = f.readlines()
            for cnt, line in enumerate(lines):
                device = {}
                line = line.rstrip("\n")
                items = line.split(",")
                if cnt == 0:
                    for item in items:
                        # print(item)
                        headers.append(item)
                else:
                    for idx, item in enumerate(items):
                        device[headers[idx]] = item
                if not line:
                    continue
                if device != {}:
                    self.devices_list.append(device)

    def write_config(self, _config: List, _hostname: str):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        outfile = self.out_dir + '/' + _hostname + '_' + timestamp + '.txt'
        with open(outfile, "w", encoding="utf-8") as f:
            for item in _config:
                f.write(str(item) + "\n")

    def create_new_config(self):
        key1 = 'hostname SW-2960L-8TS'
        key2 = 'vlan 10,247'
        key3 = 'switchport access vlan '
        key4 = 'ip address 192.168.99.2 255.255.255.0'
        key5 = 'ip default-gateway 192.168.99.1'
        key6 = 'interface Vlan99'

        for device in self.devices_list:
            created_new_config = []
            for item in self.template_config:
                if key1 in item:
                    created_new_config.append(f"hostname {device['HOSTNAME']}")
                    continue
                if key2 in item:
                    created_new_config.append(f"vlan {device['DVLAN']} {device['MVLAN']}")
                    continue
                if key3 in item:
                    created_new_config.append(f" switchport access vlan {device['DVLAN']}")
                    continue
                if key4 in item:
                    created_new_config.append(f" ip address {device['IP']} 255.255.255.0")
                    continue
                if key5 in item:
                    created_new_config.append(f" ip default-gateway {device['GATEWAY']}")
                    continue
                if key6 in item:
                    created_new_config.append(f" interface Vlan{device['MVLAN']}")
                    continue
                created_new_config.append(item)

            self.write_config(created_new_config, device['HOSTNAME'])
            # self.created_config.append(created_new_config)

    def run(self):
        self.import_template()
        self.import_input_list()
        self.create_new_config()


def main(_template: str, _devices: str, _out: str) -> None:

    create_config = CreateConfig(_template, _devices, _out)
    create_config.run()

    print('check result')
    # print('< new config >')
    # for idx, config in enumerate(create_config.created_config):
    #     print('=====', idx, '=====')
    #     for c in config:
    #         print(c)
    #     print('')
    # print('< device file >')
    for dev_info in create_config.devices_list:
        logger.info(dev_info)


if __name__ == '__main__':
    cur_dir = os.getcwd()
    template_file = os.path.join(cur_dir, "template", "2960L.txt")
    devices_file = os.path.join(cur_dir, "settings", "devices_file.txt")
    output_dir = os.path.join(cur_dir, "out")

    main(template_file, devices_file, output_dir)

    gc.collect()
