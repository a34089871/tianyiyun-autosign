import os
import time
import re
import base64
import hashlib
import rsa
import requests

BI_RM = list("0123456789abcdefghijklmnopqrstuvwxyz")

B64MAP = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"

s = requests.Session()

def get_accounts():
    username = os.getenv('CLOUD189_USERNAME')
    password = os.getenv('CLOUD189_PASSWORD')
    if not username or not password:
        raise ValueError("Username or password not set in environment variables")
    return [{'username': username, 'password': password}]

accounts = get_accounts()

def int2char(a):
    return BI_RM[a]


def b64tohex(a):
    d = ""
    e = 0
    c = 0
    for i in range(len(a)):
        if list(a)[i] != "=":
            v = B64MAP.index(list(a)[i])
            if 0 == e:
                e = 1
                d += int2char(v >> 2)
                c = 3 & v
            elif 1 == e:
                e = 2
                d += int2char(c << 2 | v >> 4)
                c = 15 & v
            elif 2 == e:
                e = 3
                d += int2char(c)
                d += int2char(v >> 2)
                c = 3 & v
            else:
                e = 0
                d += int2char(c << 2 | v >> 4)
                d += int2char(15 & v)
    if e == 1:
        d += int2char(c << 2)
    return d


def rsa_encode(j_rsakey, string):
    rsa_key = f"-----BEGIN PUBLIC KEY-----\n{j_rsakey}\n-----END PUBLIC KEY-----"
    pubkey = rsa.PublicKey.load_pkcs1_openssl_pem(rsa_key.encode())
    result = b64tohex((base64.b64encode(rsa.encrypt(f'{string}'.encode(), pubkey))).decode())
    return result


def calculate_md5_sign(params):
    return hashlib.md5('&'.join(sorted(params.split('&'))).encode('utf-8')).hexdigest()


def login(username, password):
    # https://m.cloud.189.cn/login2014.jsp?redirectURL=https://m.cloud.189.cn/zhuanti/2021/shakeLottery/index.html
    url = ""
    urlToken = "https://m.cloud.189.cn/udb/udb_login.jsp?pageId=1&pageKey=default&clientType=wap&redirectURL=https://m.cloud.189.cn/zhuanti/2021/shakeLottery/index.html"
    s = requests.Session()
    r = s.get(urlToken)
    pattern = r"https?://[^\s'\"]+"  # 匹配以http或https开头的url
    match = re.search(pattern, r.text)  # 在文本中搜索匹配
    if match:  # 如果找到匹配
        url = match.group()  # 获取匹配的字符串
        # print(url)  # 打印url
    else:  # 如果没有找到匹配
        print("没有找到url")

    r = s.get(url)
    # print(r.text)
    pattern = r"<a id=\"j-tab-login-link\"[^>]*href=\"([^\"]+)\""  # 匹配id为j-tab-login-link的a标签，并捕获href引号内的内容
    match = re.search(pattern, r.text)  # 在文本中搜索匹配
    if match:  # 如果找到匹配
        href = match.group(1)  # 获取捕获的内容
        # print("href:" + href)  # 打印href链接
    else:  # 如果没有找到匹配
        print("没有找到href链接")

    r = s.get(href)
    captchaToken = re.findall(r"captchaToken' value='(.+?)'", r.text)[0]
    lt = re.findall(r'lt = "(.+?)"', r.text)[0]
    returnUrl = re.findall(r"returnUrl= '(.+?)'", r.text)[0]
    paramId = re.findall(r'paramId = "(.+?)"', r.text)[0]
    j_rsakey = re.findall(r'j_rsaKey" value="(\S+)"', r.text, re.M)[0]
    s.headers.update({"lt": lt})

    username = rsa_encode(j_rsakey, username)
    password = rsa_encode(j_rsakey, password)
    url = "https://open.e.189.cn/api/logbox/oauth2/loginSubmit.do"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:74.0) Gecko/20100101 Firefox/76.0',
        'Referer': 'https://open.e.189.cn/',
    }
    data = {
        "appKey": "cloud",
        "accountType": '01',
        "userName": f"{{RSA}}{username}",
        "password": f"{{RSA}}{password}",
        "validateCode": "",
        "captchaToken": captchaToken,
        "returnUrl": returnUrl,
        "mailSuffix": "@189.cn",
        "paramId": paramId
    }
    r = s.post(url, data=data, headers=headers, timeout=5)
    if (r.json()['result'] == 0):
        print(r.json()['msg'])
    else:
        print(r.json()['msg'])
        print(r.json())
    redirect_url = r.json()['toUrl']
    r = s.get(redirect_url)
    return s


def main():
    for account in accounts:
        username = account["username"]
        password = account["password"]
        s = login(username, password)
        if s is not None:
            rand = str(round(time.time() * 1000))
            surl = f'https://api.cloud.189.cn/mkt/userSign.action?rand={rand}&clientType=TELEANDROID&version=8.6.3&model=SM-G930K'
            url = f'https://m.cloud.189.cn/v2/drawPrizeMarketDetails.action?taskId=TASK_SIGNIN&activityId=ACT_SIGNIN'
            url2 = f'https://m.cloud.189.cn/v2/drawPrizeMarketDetails.action?taskId=TASK_SIGNIN_PHOTOS&activityId=ACT_SIGNIN'
            url3 = f'https://m.cloud.189.cn/v2/drawPrizeMarketDetails.action?taskId=TASK_2022_FLDFS_KJ&activityId=ACT_SIGNIN'
            headers = {
                'User-Agent': 'Mozilla/5.0 (Linux; Android 5.1.1; SM-G930K Build/NRD90M; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/74.0.3729.136 Mobile Safari/537.36 Ecloud/8.6.3 Android/22 clientId/355325117317828 clientModel/SM-G930K imsi/460071114317824 clientChannelId/qq proVersion/1.0.6',
                "Referer": "https://m.cloud.189.cn/zhuanti/2016/sign/index.jsp?albumBackupOpened=1",
                "Host": "m.cloud.189.cn",
                "Accept-Encoding": "gzip, deflate",
            }
            response = s.get(surl, headers=headers)
            print(response.text)
            netdiskBonus = response.json()['netdiskBonus']
            # isSign 返回的数据类型为bool
            if (response.json()['isSign'] == True):
                print(f"{username}已经签到过了，签到获得{netdiskBonus}M空间")
                res1 = f"{username}已经签到过了，签到获得{netdiskBonus}M空间"
            else:
                print(f"{username}签到成功，签到获得{netdiskBonus}M空间")
                res1 = f"{username}签到成功，签到获得{netdiskBonus}M空间"

            headers = {
                'User-Agent': 'Mozilla/5.0 (Linux; Android 5.1.1; SM-G930K Build/NRD90M; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/74.0.3729.136 Mobile Safari/537.36 Ecloud/8.6.3 Android/22 clientId/355325117317828 clientModel/SM-G930K imsi/460071114317824 clientChannelId/qq proVersion/1.0.6',
                "Referer": "https://m.cloud.189.cn/zhuanti/2016/sign/index.jsp?albumBackupOpened=1",
                "Host": "m.cloud.189.cn",
                "Accept-Encoding": "gzip, deflate",
            }
            response = s.get(url, headers=headers)
            print(response.text)
            if ("errorCode" in response.text):
                print(response.json()["errorCode"])
                res2 = "抽奖失败,次数不足"
            else:
                prizeName = response.json()['prizeName']
                print(f"第1次抽抽奖获得{prizeName}")
                res2 = f"第1次抽抽奖获得{prizeName}"

        #第二次抽奖
        time.sleep(5)
        response = s.get(url2, headers=headers)
        print(response.text)
        if ("errorCode" in response.text):
            print(response.json()["errorCode"])
            res3 = "抽奖失败,次数不足"
        else:
            prizeName = response.json()['prizeName']
            print(f"第2次抽抽奖获得{prizeName}")
            res3 = f"第2次抽抽奖获得{prizeName}"
        #第三次抽奖
        time.sleep(5)
        response = s.get(url3, headers=headers)
        print(response.text)
        if ("errorCode" in response.text):
            print(response.json()["errorCode"])
            res4 = "抽奖失败,次数不足。"
        else:
            prizeName = response.json()['prizeName']
            print(f"第3次抽奖获得{prizeName}")
            res4 = f"第3次抽奖获得{prizeName}"

        #输出信息
        result_list = [res1, res2, res3, res4]
        result_string = "。".join(result_list)
        print(result_string)
        title = f"【天翼】{username}"



if __name__ == "__main__":
    # time.sleep(random.randint(5, 30))
    main()
