import re


headers = {
    'accept': '*/*',
    'accept-language': 'en-US;q=0.9,en;q=0.8,id;q=0.7',
    'priority': 'u=1, i',
    'origin': 'https://tte.dogiators.com',
    'referer': 'https://tte.dogiators.com/',
    'sec-ch-ua-mobile': '?1',
    'sec-ch-ua-platform': '"Android"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'x-requested-with': 'org.telegram.messenger'
}


def get_sec_ch_ua(user_agent):
    pattern = r'(Chrome|Chromium)\/(\d+)\.(\d+)\.(\d+)\.(\d+)'

    match = re.search(pattern, user_agent)

    if match:
        browser = match.group(1)
        version = match.group(2)

        if browser == 'Chrome':
            sec_ch_ua = f'"Chromium";v="{version}", "Not;A=Brand";v="24", "Google Chrome";v="{version}"'
        else:
            sec_ch_ua = f'"Chromium";v="{version}", "Not;A=Brand";v="24"'

        return {'sec-ch-ua': sec_ch_ua}
    else:
        return {}
