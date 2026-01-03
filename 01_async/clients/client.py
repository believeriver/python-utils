import os
import sys
import asyncio
import gc
import datetime
import logging
import json
from optparse import OptionParser

dir_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(dir_path)

from config import settings
from tools import utils_slurm

logging.basicConfig(
        stream=sys.stdout,
        level=logging.INFO,
        format='%(asctime)s:%(name)s:%(levelname)s:%(message)s')
logger = logging.getLogger(__name__)

"""
Created by Me.
email:
ver: 1.0
date: 2024.10.03
"""


class AwaitableClass(object):
    def __init__(self, arg, _loop):
        self.name = str(arg[0])
        self.num = str(arg[1])
        self.hostname = str(arg[2])
        self._send_msg = send_msg = self.name + "," + self.num + "," + self.hostname
        self.loop = _loop
        self._ip = settings.SERVER_IP
        self._port = settings.SERVER_PORT

    def __await__(self):
        async def request_server():
            try:
                reader, writer = await asyncio.open_connection(
                    self._ip, self._port)
                writer.write(self._send_msg.encode())
                writer.write_eof()
                data = await reader.read()
                data = data.decode()
                return data
            except Exception as e:
                _messages = "The server-side service may be down, so please contact support."
                logger.error({"ERROR:__AwaitableClass__": _messages})
        return request_server().__await__()


async def main(name, _loop):
    print('='*100)
    print('---> check ansys log, please wait...\n')
    result = await AwaitableClass(name, _loop)
    print(result)
    print('---> finish')


def fetch_input_data():
    usage = 'usage: %prog -u <username> -n <number> -j <Slurm job ID> -v'
    parser = OptionParser(usage=usage)

    parser.add_option('-u', '--user', action='store', type='string',
                      dest='name', help='user name')
    parser.add_option('-n', '--num', action='store', type='int',
                      dest='num', help='tail number')
    parser.add_option('-j', '--jobid', action='store', type='int',
                      dest='jobid', help='slurm job id')
    parser.add_option('-v', '--verbose', action='store_true',
                      dest='verbose', default=False,
                      help='verbose slurm information')

    options, args = parser.parse_args()

    username = str(options.name)
    nums = int(options.num)
    jobid = int(options.jobid)
    verbose = options.verbose
    if username is None or username == "None":
        raise Exception("user name is required.")

    logger.debug({'username': username})
    logger.debug({'nums': nums})
    logger.debug({'jobID': jobid})
    logger.debug({'verbose': verbose})

    return username, nums, jobid, verbose


if __name__ == '__main__':

    """ Sample usage:
    (.venv) clients$ python client.py -u user -n 20 -j 0
    check start :2026/01/04 07:12:15
    ====================================================================================================
    ---> check ansys log, please wait...
    
    2026-01-04 07:12:07,379:__main__:INFO:{'Executing command': 'cat ~/server/log/server.log | grep user | tail -n 20'}
    2026-01-04 07:12:07,402:__main__:INFO:{'status': 'success', 'client_ip': '127.0.0.1', 'name': 'user', 'num': '20', 'hostname': 'NAN'}
    2026-01-04 07:12:15,145:__main__:INFO:{'Executing command': 'cat ~/server/log/server.log | grep user | tail -n 20'}
    
    ---> finish
    (.venv) clients$ python client.py -u user -n 20 -j 0 -v
    check start :2026/01/04 07:12:35
    ====================================================================================================
    ---> check ansys log, please wait...
    
    2026-01-04 07:12:07,379:__main__:INFO:{'Executing command': 'cat ~/server/log/server.log | grep user | tail -n 20'}
    2026-01-04 07:12:07,402:__main__:INFO:{'status': 'success', 'client_ip': '127.0.0.1', 'name': 'user', 'num': '20', 'hostname': 'NAN'}
    2026-01-04 07:12:15,145:__main__:INFO:{'Executing command': 'cat ~/server/log/server.log | grep user | tail -n 20'}
    2026-01-04 07:12:15,164:__main__:INFO:{'status': 'success', 'client_ip': '127.0.0.1', 'name': 'user', 'num': '20', 'hostname': 'NAN'}
    2026-01-04 07:12:35,622:__main__:INFO:{'Executing command': 'cat ~/server/log/server.log | grep user | tail -n 20'}
    
    ---> finish
    (.venv) clients$ 
    """

    username = None
    nums = None
    jobid = None
    hostname = "NAN"
    slurm_user = None

    dt_now = datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')
    print(f'check start :{dt_now}')

    try:
        username, nums, jobid, verbose = fetch_input_data()
        logger.debug({
            'usename': username,
            'length': nums,
            'jobid': jobid,
            'verbose': verbose,
            })

        if jobid > 0:
            dataset = utils_slurm.fetch_slurm_job_info(int(jobid))
            hostname = dataset['HOSTNAME']
            slurm_user = dataset['User']
            logger.debug({'Slurm user name': slurm_user})
            if verbose:
                print('='*100)
                print('* slurm job information *')
                print(json.dumps(dataset, indent=2))

        logger.debug({'your account name': username})
        logger.debug({'hostname': hostname})

        if slurm_user is not None and slurm_user != username:
            messages = f" Slurm user name({slurm_user}) is not match your account name({username})."
            messages = messages + " Please check job id."
            raise Exception(messages)

        loop = asyncio.get_event_loop()
        loop.run_until_complete(asyncio.wait([
            main([username, nums, hostname], loop),
        ]))
        loop.close()
    except Exception as e:
        logger.error(str(e))

    gc.collect()
