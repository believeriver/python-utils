import asyncio
import asyncio.subprocess
import shlex
import logging
import sys
import os
import datetime
import gc
import re

dir_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(dir_path)

from config import settings

#logging.basicConfig(filename=settings.LOG_FILE, level=logging.DEBUG)
logging.basicConfig(
        filename=settings.LOG_FILE,
        level=logging.INFO,
        format='%(asctime)s:%(name)s:%(levelname)s:%(message)s')
logger = logging.getLogger(__name__)
logger.debug({'add path': dir_path})

"""
Created: 
email:
ver: 1.0
date: 2024.10.01
"""


class FetchLogAPIServer(object):
    def __init__(self, _base_command, _strlen, _hostname_strlen, _timeout):
        self.lock = asyncio.Lock()
        self.base_command = _base_command
        self.strlen = _strlen
        self.timeout = _timeout
        self._hostname_len = _hostname_strlen

    @staticmethod
    def is_valid_string(text):
        pattern = r'^[a-zA-Z0-9-]+$'
        if re.match(pattern, text):
            return True
        else:
            return False

    async def run_command(self, reader, writer):
        dt_now = datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')
        try:
            data = await reader.read()
            client_addr = writer.get_extra_info('peername')
            client_ip = client_addr[0]
            client_port = client_addr[1]
            logger.debug({'time': dt_now, 'client_ip': client_ip, 'client_port': client_port})
            rev_msg = data.decode()
            logger.debug(rev_msg)
            name, num, hostname = rev_msg.split(',')
            print({
                'time': dt_now,
                'client_ip': client_ip,
                'name': name,
                'num': num,
                'hostname': hostname})
            logger.debug({
                'input name': name,
                'input num': num,
                'hostname': hostname})

            if not name.isalnum() or len(name) > int(self.strlen):
                logger.error({
                    'status': 'failed',
                    'client ip': client_ip,
                    '[ERROR]Bad name': name})
                raise ValueError(f"{name} is an Invalid or Too long input")

            if not num.isdigit():
                logger.error({
                    'status': 'failed',
                    'client ip': client_ip,
                    '[ERROR]Bad num': num})
                raise ValueError(f"{num} is not number.")

            if not self.is_valid_string(hostname) or len(hostname) > int(self._hostname_len):
                logger.error({
                    'status': 'failed',
                    'client ip': client_ip,
                    '[ERROR]Bad hostname': hostname})
                raise ValueError(f"{hostname} is an Invalid or Too long input.")

            full_command = self.base_command + shlex.quote(name)
            if hostname != 'NAN':
                full_command = full_command + ' | grep ' + shlex.quote(hostname)
            full_command = full_command + ' | tail -n ' + shlex.quote(num)
            logger.info({"Executing command": full_command})

            async with self.lock:
                proc = await asyncio.create_subprocess_exec(
                    'sh', '-c', full_command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE)
                try:
                    stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=self.timeout)
                    res = str(stdout.decode())
                    exitcode = await proc.wait()
                    if proc.returncode != 0:
                        error_message = f"Command failed with exit code {exitcode}: {stderr.decode()}"
                        logger.error({
                            'status': 'failed',
                            'client ip': client_ip,
                            '[ERROR]Command failed': full_command})
                        writer.write(error_message.encode())
                    else:
                        writer.write(res.encode())
                        logger.info({
                            'status': 'success',
                            'client_ip': client_ip,
                            'name': name,
                            'num': num,
                            'hostname': hostname})
                except asyncio.TimeoutError:
                    proc.kill()
                    logger.error({
                        'status': 'failed',
                        'client ip': client_ip,
                        "[ERROR]Command time out": full_command})
                    writer.write("Command timed out".encode())
        except Exception as e:
            logger.error({
                'status': 'failed',
                "[ERROR]Catch Exception": str(e)})
            writer.write(f"Error: {str(e)}".encode())
        finally:
            await writer.drain()
            writer.close()


if __name__ == '__main__':
    """Sample
    server$ python server.py 
    server ('127.0.0.1', 8888)
    {'time': '2026/01/04 07:12:07', 'client_ip': '127.0.0.1', 'name': 'user', 'num': '20', 'hostname': 'NAN'}
    {'time': '2026/01/04 07:12:15', 'client_ip': '127.0.0.1', 'name': 'user', 'num': '20', 'hostname': 'NAN'}
    {'time': '2026/01/04 07:12:35', 'client_ip': '127.0.0.1', 'name': 'user', 'num': '20', 'hostname': 'NAN'}
    """
    ip = settings.SERVER_IP
    port = settings.SERVER_PORT
    base_command = settings.BASE_COMMAND
    timeout = settings.TIMEOUT
    strlen = settings.STR_LEN_LIMIT
    hostname_strlen = 20

    loop = asyncio.get_event_loop()
    counter_sever = FetchLogAPIServer(
            base_command, strlen, hostname_strlen, timeout)
    coro = asyncio.start_server(counter_sever.run_command,
                                ip, port, loop=loop)

    server = loop.run_until_complete(coro)
    print('server {}'.format(server.sockets[0].getsockname()))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    server.close()
    loop.run_until_complete(server.wait_closed())
    loop.close()

    gc.collect()
