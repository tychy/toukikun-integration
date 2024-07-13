import json
import os
import urllib.request
import re
from datetime import datetime

def lambda_handler(event, context):
    body = json.loads(event['body'])
    if 'type' in body and body['type'] == 'url_verification':
        return {
            'statusCode': 200,
            'body': json.dumps({'challenge': body['challenge']})
        }
    
    # イベントの処理
    if 'event' in body and body['event']['type'] == 'app_mention':
        text = body['event']['text']
        user = body['event']['user']
        channel = body['event']['channel']
        
        # "@toukikun "の部分を除去
        message = text.split(' ', 1)[1] if ' ' in text else ''
        # 空白を削除
        message = message.strip()
        message_handler(channel, user, message)
    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'Event processed'})
    }

def message_handler(channel, user, message):
    # help
    if message == 'help':
        send_message_to_slack(channel, f'<@{user}> 実行例\n登記簿取得: @Toukikun 1234567890123\n課金対象の登記簿取得数: @Toukikun usage')
        return
    
    # 利用量
    if message == 'usage':
        current_month_usage = get_current_usage()
        previous_month_usage = get_previous_usage()
        send_message_to_slack(channel, f'<@{user}> 当月: {current_month_usage}件 前月:{previous_month_usage}件')
        return
    
    # 登記簿取得
    # 13桁の数字であるかチェック
    if re.match(r'^\d{13}$', message):
        response_text = f'<@{user}> 登記簿取得を開始します。法人番号: {message}'
        send_message_to_slack(channel, response_text)
        toukikun_text = get_toukibo(message)
        send_message_to_slack(channel, f"<@{user}> {toukikun_text}")
        return
    else:
        response_text = f'<@{user}> 法人番号として13桁の数字を入力してください。入力: {message}'
        send_message_to_slack(channel, response_text)
        return


def send_message_to_slack(channel, text):
    slack_url = 'https://slack.com/api/chat.postMessage'
    payload = {
        'channel': channel,
        'text': text,
        'token': os.environ['VERIFICATION_TOKEN']
    }
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {os.environ['BOT_USER_OAUTH_TOKEN']}'
    }
    
    req = urllib.request.Request(slack_url, 
                                 data=json.dumps(payload).encode('utf-8'), 
                                 headers=headers, 
                                 method='POST')
    
    with urllib.request.urlopen(req) as response:
        return response.read().decode('utf-8')

def get_toukibo(code):
    url = 'https://test.tychy.jp/v1/toukikun/9011001155105'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {os.environ['TOUKIKUN_API_TOKEN']}',
        'User-Agent': 'toukikun-slack-app',
    }
    
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            
            # 時刻を読みやすく
            dt = datetime.fromisoformat(data['published_at'].replace('Z', '+00:00'))
            readable_datetime = dt.strftime('%Y年%m月%d日 %H時%M分%S秒')
            
            # 役員を読みやすく
            houjin_executive_names = '　'.join(data['houjin_executive_names'])
            
            # 代表者氏名を読みやすく
            houjin_representative_names = '　'.join(data['houjin_representative_names'])

            return f"""法人番号{code}の登記簿取得が成功しました。
登記簿発行時刻: {readable_datetime}
登記簿URL: <{data['signed_url']}|URL> (有効期限3日)
リクエストID: {data['request_id']}
ファイルID: {data['file_id']}
法人名　　: {data['houjin_name']}
法人格　　: {data['houjin_kaku']}
法人住所　: {data['houjin_address']}
資本金　　: {data['houjin_capital']}
役員　　　: {houjin_executive_names}
代表者　　: {houjin_representative_names}
法人設立日: {data['houjin_created_at']}
法人破産日: {data['houjin_bankrupted_at']}
法人解散日: {data['houjin_dissolved_at']}
会社継続日: {data['houjin_continued_at']}"""
    except urllib.error.HTTPError as e:
        return 'エラーが発生しました: {} {}'.format(e.code, e.reason)
    except Exception as e:
        return '予期せぬエラーが発生しました: {}'.format(str(e))

def get_usage(url):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {os.environ['TOUKIKUN_API_TOKEN']}',
        'User-Agent': 'toukikun-slack-app',
    }
    req = urllib.request.Request(url, headers=headers, method='GET')
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            return data['count']
    except urllib.error.HTTPError as e:
        return 'エラーが発生しました: {} {}'.format(e.code, e.reason)
    except Exception as e:
        return '予期せぬエラーが発生しました: {}'.format(str(e))

def get_current_usage():
    url = 'https://test.tychy.jp/v1/currentmonthusage'
    return get_usage(url)

def get_previous_usage():
    url = 'https://test.tychy.jp/v1/previousmonthusage'
    return get_usage(url)


