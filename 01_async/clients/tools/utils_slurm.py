import subprocess
from subprocess import PIPE
import logging
import time
import datetime
import os
import sys
import gc
import re
import json

dir_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(dir_path)

handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(asctime)s:%(name)s:%(levelname)s:%(message)s')
handler.setFormatter(formatter)

logger = logging.getLogger(__name__)
#logger.setLevel(logging.DEBUG)
logger.setLevel(logging.INFO)
logger.addHandler(handler)


logger.debug({'add path': dir_path})

"""
Created by Me.
email:
ver: 1.0
date: 2024.10.01
"""


class FetchSlurmJobInformation(object):
    def __init__(self, _jobid):
        self._starttime = '2022-01-01'
        self._endtime = self._fetch_tomorrow()
        self._jobid = _jobid
        self._sacct_info = None
        self.sacct_data = dict()

        logger.debug(self._endtime)
        logger.debug(self._jobid)
        logger.debug({"now": self._endtime})

    @staticmethod
    def _fetch_tomorrow():
        today = datetime.datetime.now()
        tomorrow = today + datetime.timedelta(days=1)
        return tomorrow.date()

    def _submit_sacct(self):

        logger.debug(str(self._jobid))
        _command = '\sacct -j ' + str(self._jobid)
        _command = _command + ' --starttime=' + str(self._starttime)
        _command = _command + ' --endtime=' + str(self._endtime)
        _command = _command + ' --format JobID%10,end%16,JobName%20,User%8,NodeList%30,state -X'
        logger.debug({
            'action': "_submit_acct",
            'command': _command})
        saccts = subprocess.run(
                _command,
                shell=True,
                stdout=PIPE,
                universal_newlines=True).stdout.split('\n')

        if len(saccts) < 4:
            logger.error({'action': 'sacct','status': 'failed'})
            raise Exception('There is no sacct data.')

        item_name = []
        for item in saccts[0].split():
            item_name.append(item)

        for idx,item in enumerate(saccts[2].split()):
            #print(idx, item_name[idx], "".join(item.split()))
            logger.debug({
                "action" : "_submit_sacct",
                "idx":idx,
                "item_name":item_name[idx],
                "value": "".join(item.split())})
            self.sacct_data[item_name[idx]] = "".join(item.split())
        logger.debug(self.sacct_data)

    def _pickup_headnode(self):

        nodelist = self.sacct_data['NodeList']
        #test data
        #nodelist = "h11n[001,005-010]"
        #nodelist = "r4s-h17235n[001,005-010]"
        #nodelist = "r4s-h17235n014"
        #nodelist = "h11n001"
        #

        items = nodelist.split('[')
        logger.debug({
            "action":"_picup_headnode",
            "items":items,
            "len(items)":len(items)})

        if len(items)<2:
            temp = nodelist.split(',')
            if len(temp)<2:
                self.sacct_data['HOSTNAME'] = nodelist
            else:
                logger.debug({'action':'pickup_headnode','value': temp})
                self.sacct_data['HOSTNAME'] = temp[0]
        else:
            indexes = re.split(r'[\[,\]-]', items[1])
            self.sacct_data['HOSTNAME'] = items[0] + indexes[0]
        logger.debug(self.sacct_data['HOSTNAME'])

    def run(self):

        self._submit_sacct()
        self._pickup_headnode()

    def __str__(self):
        #return '\n'.join(f'{k}: {v}' for k, v in self.sacct_data.items())
        return json.dumps(self.sacct_data, indent=2)


def fetch_slurm_job_info(jobid):

    result = None
    try:
        logger.debug({"job id": jobid})
        slurm_info = FetchSlurmJobInformation(jobid)
        slurm_info.run()
        #logger.debug(slurm_info)
        result = slurm_info.sacct_data
    except Exception as e:
        logger.error(str(e))

    finally:
        return result


if __name__ == '__main__':
    timeout = 10
    dt_now = datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')

    for jobid in range(0, 14):
        print(jobid)
        res = fetch_slurm_job_info(jobid)
        if res is None:
            print('result : No data')
        else:
            print(json.dumps(res, indent=2))