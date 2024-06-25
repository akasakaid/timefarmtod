import os
import sys
import json
import time
import requests
from colorama import *
from datetime import datetime
from urllib.parse import parse_qs
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
            "Host": "tg-bot-tap.laborx.io",
            "Connection": "keep-alive",
            "User-Agent": "",
            "Content-Type": "text/plain;charset=UTF-8",
            "Accept": "*/*",
            "Origin": "https://tg-tap-miniapp.laborx.io",
            "X-Requested-With": "org.telegram.messenger",
            "Sec-Fetch-Site": "same-site",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "Referer": "https://tg-tap-miniapp.laborx.io/",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "en,en-US;q=0.9",
        }
        self.marin_kitagawa = lambda data: {
            k: v[0] for k, v in parse_qs(data).items()}
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
        uar = UserAgent(software_names=software,
                        operating_systems=operating, limit=100)
        ua = uar.get_random_user_agent()
        return ua

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
            start_farming = res.json(
            )["activeFarmingStartedAt"].replace("Z", "")
            start_farming_ts = int(
                datetime.fromisoformat(start_farming).timestamp())
            farming_duration = res.json()["farmingDurationInSec"]
            end_farming = start_farming_ts + farming_duration
            end_farming_iso = datetime.fromtimestamp(end_farming)
            countdown = end_farming - now
            self.log(f"{hijau}end farming at : {putih}{end_farming_iso}")
            return countdown

        start_farming = start_farming.replace("Z", "")
        start_farming_ts = int(
            datetime.fromisoformat(start_farming).timestamp())
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
            start_farming = res.json(
            )["activeFarmingStartedAt"].replace("Z", "")
            start_farming_ts = int(
                datetime.fromisoformat(start_farming).timestamp())
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
            self.log(
                f'{merah}token not found in response, maybe your data invalid !')
            return False

        self.log(f'{hijau}success renew token !')
        token = res.json()["token"]
        daily = res.json()['dailyRewardInfo']
        self.user_level = res.json()['info']['level']
        self.level_upgrade = res.json()['levelDescriptions']
        self.user_balance = res.json()['balanceInfo']['balance']
        self.log(f'{hijau}balance : {putih}{self.user_balance}')
        self.log(f'{hijau}level : {putih}{self.user_level}')
        if daily is not None:
            rew = daily['reward']
            headers['authorization'] = f"Bearer {token}"
            daily_url = "https://tg-bot-tap.laborx.io/api/v1/me/onboarding/complete"
            res = self.http(daily_url, headers, json.dumps({}))
            if res.status_code == 200:
                self.log(f'{hijau}success claim daily, reward {putih}{rew}!')

        return token

    def upgrade_level(self, token):
        headers = self.headers.copy()
        headers['authorization'] = f"Bearer {token}"
        if int(self.user_level) == int(self.level_upgrade[len(self.level_upgrade) - 1]['level']):
            self.log(f'{kuning}you already get max level !')
            return
        for level in self.level_upgrade:
            if int(self.user_level) >= int(level['level']):
                continue

            if level['price'] > self.user_balance:
                self.log(f'{kuning}balance not enough to upgrade !')
                break

            upgrade_url = "https://tg-bot-tap.laborx.io/api/v1/me/level/upgrade"

            res = self.http(upgrade_url, headers, json.dumps({}))
            if res.status_code == 200:
                self.log(f"{hijau}success upgrade to level {level['level']}")
                self.user_balance -= level['price']
                self.user_level = int(level['level'])
                continue
            self.log(f"{merah}failed upgrade to level {level['level']}")

    def main(self):
        banner = f"""
    {hijau}Auto Claim {putih}Time Farm {hijau}/ {putih}TimeFarmCryptoBot
    
    {biru}By : {putih}t.me/@AkasakaID
    {biru}Github : {putih}@AkasakaID
    
    {hijau}Message : {putih}dont forget to 'git pull' maybe the script have update !
        """
        arg = sys.argv
        if "marin" not in arg:
            os.system("cls" if os.name == "nt" else "clear")
        print(banner)
        print(self.line)
        config = json.loads(open("config.json").read())
        auto_upgrade = config["auto_upgrade"]
        auto_task = config["auto_task"]
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
                parser = self.marin_kitagawa(data)
                user = json.loads(parser["user"])
                userid = str(user["id"])
                if userid not in tokens.keys():
                    user_ua = self.get_ua()
                    self.headers["User-Agent"] = user_ua
                    user_token = self.get_token(data)
                    if user_token is False:
                        continue
                    tokens[userid] = {}
                    tokens[userid]["ua"] = user_ua
                    open("tokens.json", "w").write(
                        json.dumps(tokens, indent=4))
                user_ua = tokens[userid]["ua"]
                self.headers["User-Agent"] = user_ua
                self.log(f"{hijau}login as : {putih}{user['first_name']}")
                user_token = self.get_token(data)
                if user_token is False:
                    continue
                if auto_task:
                    self.get_task(user_token)
                curse = self.get_farming(user_token)
                if auto_upgrade:
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
            print(f"{putih}waiting until {jam}:{menit}:{detik} ",
                  flush=True, end="\r")
            t -= 1
            time.sleep(1)
        print("                          ", flush=True, end="\r")

    def http(self, url, headers, data=None):
        while True:
            try:
                if data is None:
                    headers["Content-Length"] = "0"
                    res = requests.get(url, headers=headers, timeout=30)
                    open('http.log', 'a', encoding='utf-8').write(res.text + '\n')
                    return res

                if data == "":
                    res = requests.post(url, headers=headers, timeout=30)
                    open('http.log', 'a', encoding='utf-8').write(res.text + '\n')
                    return res

                res = requests.post(url, headers=headers,
                                    data=data, timeout=30)
                open('http.log', 'a', encoding='utf-8').write(res.text + '\n')
                return res
            except (
                requests.exceptions.ConnectionError,
                requests.exceptions.Timeout
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
