import os
import sys
import json
import time
import random
import argparse
import requests
from glob import glob
from pathlib import Path
from colorama import *
from datetime import datetime
from urllib.parse import parse_qs, unquote
from telethon.sync import TelegramClient
from telethon.tl.functions.messages import RequestWebViewRequest
from random_user_agent.user_agent import UserAgent
from random_user_agent.params import SoftwareName, OperatingSystem
from telethon.errors import SessionPasswordNeededError

init(autoreset=True)

hitam = Fore.LIGHTBLACK_EX
hijau = Fore.LIGHTGREEN_EX
merah = Fore.LIGHTRED_EX
kuning = Fore.LIGHTYELLOW_EX
biru = Fore.LIGHTBLUE_EX
putih = Fore.LIGHTWHITE_EX
reset = Style.RESET_ALL


class TimeFarm:
    def __init__(self):
        self.headers = {
            "user-agent": "Mozilla/5.0 (Linux; Android 10; Redmi 4A / 5A Build/QQ3A.200805.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/86.0.4240.185 Mobile Safari/537.36",
            "content-type": "application/json",
            "accept": "*/*",
            "origin": "https://tg-tap-miniapp.laborx.io",
            "x-requested-with": "tw.nekomimi.nekogram",
            "sec-fetch-site": "same-site",
            "sec-fetch-mode": "cors",
            "sec-fetch-dest": "empty",
            "referer": "https://tg-tap-miniapp.laborx.io/",
            "accept-encoding": "gzip, deflate",
            "accept-language": "en,en-US;q=0.9",
        }
        self.marin_kitagawa = lambda data: {k: v[0] for k, v in parse_qs(data).items()}
        self.line = putih + "~" * 50
        self.session_folder = "sessions"
        self.peer = "TimeFarmCryptoBot"

    def cvdate(self, date):
        return datetime.strptime(date, "%a, %d %b %Y %H:%M:%S %Z").timestamp()

    def get_ua(self):
        software = [
            SoftwareName.CHROME.value,
            SoftwareName.EDGE.value,
        ]
        operating = [
            OperatingSystem.ANDROID.value,
            OperatingSystem.WINDOWS.value,
            OperatingSystem.IOS.value,
        ]
        uar = UserAgent(software_names=software, operating_systems=operating, limit=100)
        ua = uar.get_random_user_agent()
        return ua

    def telegram(self, phone, return_data):
        app_version = "5.1.7 x64"
        if not os.path.exists("devices.txt"):
            content = requests.get(
                "https://gist.githubusercontent.com/akasakaid/433880f5d5009444c0100a326563614f/raw/83175f60797e9c7696ed50c651cb6c0286a20177/devices.txt"
            )
            open("devices.txt", "w").write(content.text)
        device = random.choice(open("devices.txt").read().splitlines())
        if not os.path.exists(self.session_folder):
            os.makedirs(self.session_folder)

        client = TelegramClient(
            f"{self.session_folder}/{phone}",
            api_id=self.api_id,
            api_hash=self.api_hash,
            device_model=device,
            app_version=app_version,
            system_version="Windows 10",
            lang_code="us",
            system_lang_code="en-US",
        )
        try:
            client.connect()
            if not client.is_user_authorized():
                try:
                    client.send_code_request(phone=phone)
                    code = input(f"    {reset}input login code : ")
                    client.sign_in(phone=phone, code=code)
                except SessionPasswordNeededError:
                    pw2fa = input(f"    {reset}input password 2fa : ")
                    client.sign_in(phone=phone, password=pw2fa)

            if return_data is False:
                me = client.get_me()
                first_name = me.first_name
                print(f"    {hijau}login as {putih}{first_name}")
                if client.is_connected():
                    client.disconnect()
                    return True

            tgdata = (
                client(
                    RequestWebViewRequest(
                        peer=self.peer,
                        bot=self.peer,
                        platform="Android",
                        url="https://tg-tap-miniapp.laborx.io/",
                        from_bot_menu=False,
                    )
                )
                .url.split("#tgWebAppData=")[1]
                .split("&tgWebAppVersion=")[0]
            )
            if client.is_connected():
                client.disconnect()
            return unquote(tgdata)
        except Exception as e:
            self.log(e.__str__())
            return False

    def get_task(self, token):
        url_task = "https://tg-bot-tap.laborx.io/api/v1/tasks"
        headers = self.headers.copy()
        headers["Authorization"] = f"Bearer {token}"
        res = self.http(url_task, headers)
        for task in res.json():
            task_id = task["id"]
            task_title = task["title"]
            task_type = task["type"]
            if task_type == "TELEGRAM":
                continue
            if "submission" in task.keys():
                status = task["submission"]["status"]
                if status == "CLAIMED":
                    self.log(f"{kuning}already complete {task_title}")
                    continue

                if status == "COMPLETED":
                    url_claim = (
                        f"https://tg-bot-tap.laborx.io/api/v1/tasks/{task_id}/claims"
                    )
                    data = json.dumps({})
                    headers["Content-Length"] = str(len(data))
                    res = self.http(url_claim, headers, data)
                    if res.text.lower() == "ok":
                        self.log(f"{hijau}success claim reward {task_title}")
                        continue

            url_submit = (
                f"https://tg-bot-tap.laborx.io/api/v1/tasks/{task_id}/submissions"
            )
            data = json.dumps({})
            headers["Content-Length"] = str(len(data))
            res = self.http(url_submit, headers, data)
            if res.text.lower() != "ok":
                self.log(f"{merah}failed send submission {task_title}")
                continue

            url_task = f"https://tg-bot-tap.laborx.io/api/v1/tasks/{task_id}"
            res = self.http(url_task, headers)
            status = res.json()["submission"]["status"]
            if status != "COMPLETED":
                self.log(f"{merah}task is not completed !")
                continue

            url_claim = f"https://tg-bot-tap.laborx.io/api/v1/tasks/{task_id}/claims"
            data = json.dumps({})
            headers["Content-Length"] = str(len(data))
            res = self.http(url_claim, headers, data)
            if res.text.lower() == "ok":
                self.log(f"{hijau}success claim reward {task_title}")
                continue

    def get_farming(self, token):
        url = "https://tg-bot-tap.laborx.io/api/v1/farming/info"
        headers = self.headers.copy()
        headers["Authorization"] = f"Bearer {token}"
        res = self.http(url, headers)
        start_farming = res.json()["activeFarmingStartedAt"]
        if start_farming is None:
            url_start = "https://tg-bot-tap.laborx.io/api/v1/farming/start"
            data = json.dumps({})
            res = self.http(url_start, headers, data)
            now = self.cvdate(res.headers["Date"])
            start_farming = res.json()["activeFarmingStartedAt"].replace("Z", "")
            start_farming_ts = int(datetime.fromisoformat(start_farming).timestamp())
            farming_duration = res.json()["farmingDurationInSec"]
            end_farming = start_farming_ts + farming_duration
            end_farming_iso = datetime.fromtimestamp(end_farming)
            countdown = end_farming - now
            self.log(f"{hijau}end farming at : {putih}{end_farming_iso}")
            return countdown

        start_farming = start_farming.replace("Z", "")
        start_farming_ts = int(datetime.fromisoformat(start_farming).timestamp())
        farming_duration = res.json()["farmingDurationInSec"]
        end_farming = start_farming_ts + farming_duration
        end_farming_iso = datetime.fromtimestamp(end_farming)
        now = self.cvdate(res.headers["Date"])
        countdown = end_farming - now
        if now > end_farming:
            self.log(f"{hijau}farming was end !")
            url_finish = "https://tg-bot-tap.laborx.io/api/v1/farming/finish"
            data = json.dumps({})
            headers["Content-Length"] = str(len(data))
            res = self.http(url_finish, headers, data)
            balance = res.json()["balance"]
            self.log(f"{hijau}balance after farming : {putih}{balance}")
            url_start = "https://tg-bot-tap.laborx.io/api/v1/farming/start"
            res = self.http(url_start, headers, data)
            now = self.cvdate(res.headers["Date"])
            start_farming = res.json()["activeFarmingStartedAt"].replace("Z", "")
            start_farming_ts = int(datetime.fromisoformat(start_farming).timestamp())
            farming_duration = res.json()["farmingDurationInSec"]
            end_farming = start_farming_ts + farming_duration
            end_farming_iso = datetime.fromtimestamp(end_farming)
            countdown = end_farming - now
            self.log(f"{hijau}end farming at : {putih}{end_farming_iso}")
            return countdown

        self.log(f"{kuning}farming not over yet !")
        self.log(f"{hijau}end farming at : {putih}{end_farming_iso}")
        return countdown

    def get_token(self, tg_data):
        url = "https://tg-bot-tap.laborx.io/api/v1/auth/validate-init/v2"
        headers = self.headers.copy()
        data = json.dumps(
            {
                "initData": tg_data,
                "platform": "android",
            }
        )
        res = self.http(url, headers, data)
        if "token" not in res.json().keys():
            self.log(f"{merah}token not found in response, maybe your data invalid !")
            return False

        self.log(f"{hijau}success renew token !")
        token = res.json()["token"]
        daily = res.json()["dailyRewardInfo"]
        self.user_level = res.json()["info"]["level"]
        self.level_upgrade = res.json()["levelDescriptions"]
        self.user_balance = res.json()["balanceInfo"]["balance"]
        self.log(f"{hijau}balance : {putih}{self.user_balance}")
        self.log(f"{hijau}level : {putih}{self.user_level}")
        if daily is not None:
            rew = daily["reward"]
            headers["authorization"] = f"Bearer {token}"
            daily_url = "https://tg-bot-tap.laborx.io/api/v1/me/onboarding/complete"
            res = self.http(daily_url, headers, json.dumps({}))
            if res.status_code == 200:
                self.log(f"{hijau}success claim daily, reward {putih}{rew}!")

        return token

    def upgrade_level(self, token):
        headers = self.headers.copy()
        headers["authorization"] = f"Bearer {token}"
        if int(self.user_level) == int(
            self.level_upgrade[len(self.level_upgrade) - 1]["level"]
        ):
            self.log(f"{kuning}you already get max level !")
            return
        for level in self.level_upgrade:
            if int(self.user_level) >= int(level["level"]):
                continue

            if level["price"] > self.user_balance:
                self.log(f"{kuning}balance not enough to upgrade !")
                break

            upgrade_url = "https://tg-bot-tap.laborx.io/api/v1/me/level/upgrade"

            res = self.http(upgrade_url, headers, json.dumps({}))
            if res.status_code == 200:
                self.log(f"{hijau}success upgrade to level {level['level']}")
                self.user_balance -= level["price"]
                self.user_level = int(level["level"])
                continue
            self.log(f"{merah}failed upgrade to level {level['level']}")

    def load_config(self, file):
        config = json.loads(open(file).read())
        api_id = 2040
        api_hash = "b18441a1ff607e10a989891a5462e627"
        _api_id = config["api_id"]
        _api_hash = config["api_hash"]
        self.auto_upgrade = config["auto_upgrade"]
        self.auto_task = config["auto_task"]
        if len(_api_id) <= 0:
            self.api_id = api_id
        else:
            self.api_id = _api_id
        if len(_api_hash) <= 0:
            self.api_hash = api_hash
        else:
            self.api_hash = _api_hash

    def main(self):
        arg = argparse.ArgumentParser()
        arg.add_argument("--marinkitagawa", action="store_true")
        arg.add_argument("--config", default="config.json")
        args = arg.parse_args()
        banner = f"""
    {hijau}Auto Claim {putih}Time Farm {hijau}/ {putih}TimeFarmCryptoBot
    
    {biru}By : {putih}t.me/@AkasakaID
    {biru}Github : {putih}@AkasakaID
    
    {hijau}Message : {putih}dont forget to 'git pull' maybe the script have update !
        """
        menu = f"""
    {hijau}1. {putih}Create Session
    {hijau}2. {putih}Start Bot
        """
        if not os.path.exists(self.session_folder):
            os.makedirs(self.session_folder)
        self.load_config(args.config)
        while True:
            if not args.marinkitagawa:
                os.system("cls" if os.name == "nt" else "clear")
            print(banner)
            print(self.line)
            print(menu)
            opt = input(f"    {biru}input number : {reset}")
            print(self.line)
            if opt == "1":
                phone = input(f"    {hijau}input phone : {reset}")
                self.telegram(phone, return_data=False)
                print(self.line)
                input(f"{biru}press enter to continue")
                continue
            if opt == "2":
                while True:
                    list_countdown = []
                    sessions = glob(f"{self.session_folder}/*.session")
                    tokens = json.loads(open("tokens.json", "r").read())
                    if len(sessions) <= 0:
                        self.log(
                            f"{kuning}please add data account with menu number 1 !"
                        )
                        sys.exit()
                    self.log(f"{hijau}account detected : {putih}{len(sessions)}")
                    print(self.line)
                    for no, session in enumerate(sessions):
                        self.log(
                            f"{hijau}account number {biru}{no+1}{hijau}/{biru}{len(sessions)}"
                        )
                        phone = Path(session).stem
                        data = self.telegram(phone, True)
                        if data is False:
                            print(self.line)
                            continue
                        parser = self.marin_kitagawa(data)
                        user = json.loads(parser["user"])
                        userid = str(user["id"])
                        tuser = tokens.get(userid)
                        if tuser is None:
                            user_ua = self.get_ua()
                            self.headers["user-agent"] = user_ua
                            tokens[userid] = {}
                            tokens[userid]["ua"] = user_ua
                            open("tokens.json", "w").write(json.dumps(tokens, indent=4))
                        user_ua = tokens[userid]["ua"]
                        self.headers["user-agent"] = user_ua
                        self.log(f"{hijau}login as : {putih}{user['first_name']}")
                        user_token = self.get_token(data)
                        if user_token is False:
                            continue
                        if self.auto_task:
                            self.get_task(user_token)
                        curse = self.get_farming(user_token)
                        if self.auto_upgrade:
                            self.upgrade_level(user_token)
                        list_countdown.append(curse)
                        print(self.line)
                        self.countdown(10)

                    min_countdown = min(list_countdown)
                    self.countdown(int(min_countdown))

    def countdown(self, t):
        while t:
            menit, detik = divmod(t, 60)
            jam, menit = divmod(menit, 60)
            jam = str(jam).zfill(2)
            menit = str(menit).zfill(2)
            detik = str(detik).zfill(2)
            print(f"{putih}waiting until {jam}:{menit}:{detik} ", flush=True, end="\r")
            t -= 1
            time.sleep(1)
        print("                          ", flush=True, end="\r")

    def http(self, url, headers, data=None):
        while True:
            try:
                if data is None:
                    headers["Content-Length"] = "0"
                    res = requests.get(url, headers=headers, timeout=30)
                    open("http.log", "a", encoding="utf-8").write(res.text + "\n")
                    return res

                if data == "":
                    res = requests.post(url, headers=headers, timeout=30)
                    open("http.log", "a", encoding="utf-8").write(res.text + "\n")
                    return res

                res = requests.post(url, headers=headers, data=data, timeout=30)
                open("http.log", "a", encoding="utf-8").write(res.text + "\n")
                return res
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
                self.log(f"{merah}connection error / timeout !")
                time.sleep(2)
                continue

    def log(self, msg):
        now = datetime.now().isoformat(" ").split(".")[0]
        print(f"{hitam}[{now}] {reset}{msg}")


if __name__ == "__main__":
    try:
        app = TimeFarm()
        app.main()
    except KeyboardInterrupt:
        sys.exit()
