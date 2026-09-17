"""
スイッチの死活監視（ICMP Ping + SSHログイン可否）を行うモジュール。
Inventory等の詳細収集(registration.py)とは独立した、高頻度実行を想定した軽量チェック。
対象は switch_list.csv とは別の liveness_targets.csv から読み込む。
"""

import subprocess
import platform
import time
from concurrent.futures import ThreadPoolExecutor

import paramiko

from config import Config, setup_logger
from models.switch import Switch
from models.liveness import Liveness

logger = setup_logger("liveness_check", Config.LEVEL)


def check_ping(ip_address: str, timeout: int = 2) -> tuple:
    """
    ICMP Pingで疎通確認する。戻り値: (成功したか, 応答時間ms or None)
    """
    is_windows = platform.system().lower() == "windows"
    count_flag = "-n" if is_windows else "-c"
    timeout_flag = "-w" if is_windows else "-W"
    timeout_value = str(timeout * 1000) if is_windows else str(timeout)

    cmd = ["ping", count_flag, "1", timeout_flag, timeout_value, ip_address]

    start = time.time()
    try:
        result = subprocess.run(cmd, capture_output=True, timeout=timeout + 2)
        elapsed_ms = (time.time() - start) * 1000
        success = result.returncode == 0
        return success, round(elapsed_ms, 1) if success else None
    except subprocess.TimeoutExpired:
        return False, None
    except Exception as e:
        logger.warning(f"ping実行エラー: {ip_address}: {e}")
        return False, None


def check_ssh(ip_address: str, username: str, password: str, timeout: int = 5) -> tuple:
    """
    SSHログインを試みる。戻り値: (成功したか, エラーメッセージ or None)
    コマンドは実行せず、認証成功の可否のみ確認する。
    """
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(
            ip_address, username=username, password=password,
            timeout=timeout, banner_timeout=timeout, auth_timeout=timeout,
        )
        client.close()
        return True, None
    except paramiko.AuthenticationException:
        return False, "認証失敗"
    except Exception as e:
        return False, str(e)


def _check_one_target(t: dict) -> None:
    hostname = t.get("hostname")
    ip_address = t.get("ipaddr")
    username = t.get("username") or Config.USERNAME
    password = t.get("password") or Config.PASSWORD

    switch = Switch.fetch_by_hostname(hostname)
    if switch is None:
        logger.warning(f"Switch not found in DB: {hostname}(先にCSV仮登録が必要です)")
        return

    ping_ok, ping_rtt = check_ping(ip_address)
    ssh_ok, ssh_error = check_ssh(ip_address, username, password)

    Liveness.upsert(
        switch_id=switch["id"],
        ping_ok=ping_ok, ping_rtt_ms=ping_rtt,
        ssh_ok=ssh_ok, ssh_error=ssh_error,
    )
    logger.info(f"liveness: {hostname} ping={ping_ok}({ping_rtt}ms) ssh={ssh_ok}")


def run_liveness_check(targets: list, workers: int = 20) -> None:
    """
    targets: liveness_targets.csv から読み込んだtargets_list
             ([{"hostname":..., "ipaddr":..., "username":..., "password":...}, ...])
    """
    with ThreadPoolExecutor(max_workers=workers) as executor:
        executor.map(_check_one_target, targets)
