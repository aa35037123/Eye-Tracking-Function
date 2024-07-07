import requests

TOKEN = "6355462545:AAF7_X-9X3JQnfWp_kvpKQ3eqBmNwwsa8bc"
GROUP_CHAT_ID = '-4210499714'

def telegram_bot_sendtext(bot_message):
    send_text = (
        f'https://api.telegram.org/bot{TOKEN}/sendMessage'
        f'?chat_id={GROUP_CHAT_ID}&parse_mode=Markdown&text={bot_message}'
    )

    response = requests.get(send_text)
    return response.json()

if __name__ == '__main__':
    response = telegram_bot_sendtext("Hello, World")
    print(response)