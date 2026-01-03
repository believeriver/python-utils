import os
import sys

dir_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(dir_path)


"""
Share settings
"""
#server.pyを実行するサーバのIPアドレスは適切に変更する。以下はlocalhostの設定。
#ポート番号も、既存サービスと重複しないようなものを選定する。
SERVER_IP = '127.0.0.1'
SERVER_PORT = 8888

"""
For Server settings
"""
LOG_FILE = dir_path + '/log/server.log'
LIC_FILE = dir_path + '/log/server.log'
BASE_COMMAND = 'cat ' + LIC_FILE + ' | grep '
TIMEOUT = 10
STR_LEN_LIMIT = 10
