import os
import sys
import json
import time
import random
import requests
from colorama import *
from base64 import b64decode
from datetime import datetime
from urllib.parse import unquote
from random_user_agent.user_agent import UserAgent
from random_user_agent.params import SoftwareName, OperatingSystem

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
            "host": "tg-bot-tap.laborx.io",
            "connection": "keep-alive",
            "user-agent": "",
            "content-type": "text/plain;charset=UTF-8",
            "accept": "*/*",
            "origin": "https://tg-tap-miniapp.laborx.io",
            "x-requested-with": "org.telegram.messenger",
            "sec-fetch-site": "same-site",
            "sec-fetch-mode": "cors",
            "sec-fetch-dest": "empty",
            "referer": "https://tg-tap-miniapp.laborx.io/",
            "accept-encoding": "gzip, deflate",
            "accept-language": "en,en-US;q=0.9",
        }
        self.line = putih + "~" * 50

    def cvdate(self, date):
        return datetime.strptime(date, "%a, %d %b %Y %H:%M:%S %Z").timestamp()

    def get_ua(self):
        software = [SoftwareName.CHROME.value, SoftwareName.EDGE.value,]
        operating = [
            OperatingSystem.ANDROID.value,
            OperatingSystem.WINDOWS.value,
            OperatingSystem.IOS.value,
        ]
        uar = UserAgent(software_names=software, operating_systems=operating, limit=100)
        ua = uar.get_random_user_agent()
        return ua

    def get_task(self, token):
        url_task = "https://tg-bot-tap.laborx.io/api/v1/tasks"
        headers = self.headers.copy()
        headers["authorization"] = f"Bearer {token}"
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
                    headers["content-length"] = str(len(data))
                    res = self.http(url_claim, headers, data)
                    if res.text.lower() == "ok":
                        self.log(f"{hijau}success claim reward {task_title}")
                        continue

            url_submit = (
                f"https://tg-bot-tap.laborx.io/api/v1/tasks/{task_id}/submissions"
            )
            data = json.dumps({})
            headers["content-length"] = str(len(data))
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
            headers["content-length"] = str(len(data))
            res = self.http(url_claim, headers, data)
            if res.text.lower() == "ok":
                self.log(f"{hijau}success claim reward {task_title}")
                continue

    def get_farming(self, token):
        url = "https://tg-bot-tap.laborx.io/api/v1/farming/info"
        headers = self.headers.copy()
        headers["authorization"] = f"Bearer {token}"
        res = self.http(url, headers)
        balance = res.json()["balance"]
        self.log(f"{hijau}balance : {putih}{balance}")
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
            headers["content-length"] = str(len(data))
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
        url = "https://tg-bot-tap.laborx.io/api/v1/auth/validate-init"
        headers = self.headers.copy()
        res = self.http(url, headers, tg_data)
        if "token" not in res.json().keys():
            self.log(f'{merah}token not found in response, maybe your data invalid !')
            return False
        
        self.log(f'{hijau}success renew token !')
        token = res.json()["token"]
        return token

    def parsing(self, data):
        ret = {}
        for i in unquote(data).split("&"):
            key, value = i.split("=")
            ret[key] = value

        return ret

    def token_checker(self, token):
        header, payload, sign = token.split(".")
        depayload = b64decode(payload + "==")
        jeload = json.loads(depayload)
        expired = jeload["exp"]
        now = int(datetime.now().timestamp())
        if now > int(expired):
            return False
        return True

    def main(self):
        banner = f"""
    {hijau}Auto Claim {putih}Time Farm {hijau}/ {putih}TimeFarmCryptoBot
    
    {biru}By : {putih}t.me/@AkasakaID
    {biru}Github : {putih}@AkasakaID
        
        """
        arg = sys.argv
        if "marin_istrinya_fawwaz" not in arg:
            os.system("cls" if os.name == "nt" else "clear")
        print(banner)
        print(self.line)
        while True:
            list_countdown = []
            datas = open("data.txt", "r").read().splitlines()
            tokens = json.loads(open("tokens.json", "r").read())
            if len(datas) <= 0:
                self.log(f"{kuning}please add data account in data.txt")
                sys.exit()
            self.log(f'{hijau}account detected : {putih}{len(datas)}')
            print(self.line)
            for data in datas:
                parser = self.parsing(data)
                user = json.loads(parser["user"])
                userid = str(user["id"])
                if userid not in tokens.keys():
                    user_ua = self.get_ua()
                    self.headers['user-agent'] = user_ua
                    user_token = self.get_token(data)
                    if user_token is False:
                        continue
                    tokens[userid] = {}
                    tokens[userid]["token"] = user_token
                    tokens[userid]["ua"] = user_ua
                    open("tokens.json","w").write(json.dumps(tokens,indent=4))
                user_token = tokens[userid]["token"]
                user_ua = tokens[userid]["ua"]
                is_expired = self.token_checker(user_token)
                if is_expired is False:
                    self.headers["user-agent"] = user_ua
                    user_token = self.get_token(data)
                    if user_token is False:
                        continue
                    tokens[userid]["token"] = user_token
                    open("tokens.json", "w").write(json.dumps(tokens, indent=4))
                self.log(f"{hijau}login as : {putih}{user['first_name']}")
                self.get_task(user_token)
                curse = self.get_farming(user_token)
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
                    headers["content-length"] = "0"
                    res = requests.get(url, headers=headers)
                    return res

                if data == "":
                    res = requests.post(url, headers=headers)
                    return res

                res = requests.post(url, headers=headers, data=data)
                return res
            except (
                requests.exceptions.ConnectionError,
                requests.exceptions.ConnectTimeout,
                requests.exceptions.ReadTimeout,
                requests.exceptions.ConnectTimeout,
            ):
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
