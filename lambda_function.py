import os
import re
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List

from slack_bolt import App
from slack_bolt.adapter.aws_lambda import SlackRequestHandler
from slack_bolt.response.response import BoltResponse

import notion as notion


logging.basicConfig(level=logging.WARNING)

app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET"),
)

t_delta_ = timedelta(hours=5)  # 日本時間朝4:00に日付更新
JST_ = timezone(t_delta_, "JST")
t_delta = timedelta(hours=9)
JST = timezone(t_delta, "JST")
MONTH = {
    "1": "JAN",
    "2": "FEB",
    "3": "MAR",
    "4": "APR",
    "5": "MAY",
    "6": "JUN",
    "7": "JUL",
    "8": "AUG",
    "9": "SEP",
    "10": "OCT",
    "11": "NOV",
    "12": "DEC",
}

database_id = os.environ.get(MONTH[str(datetime.now(JST_).month)])


def lambda_handler(event, context):
    slack_handler = SlackRequestHandler(app=app)
    return slack_handler.handle(event, context)


@app.use
def no_retry(context, next):
    if context.get("lambda_request", {}).get("headers", {}).get("x-slack-retry-num", False):
        return BoltResponse(status=200, body="no need retry")
    else:
        next()


def push_button(say, body, logger):
    logger.info(body)
    if body["event"]["user"] != os.environ.get("USER_ID"):
        logger.warning(f"{body['event']['user']} try to push the button.")
        return BoltResponse(status=200)

    channel: str = body["event"]["channel"]

    say(
        channel=channel,
        text="yahho-",
        blocks=[
            {
                "type": "section",
                "block_id": "new",
                "text": {"type": "mrkdwn", "text": "出勤はまだか。"},
                "accessory": {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "出勤", "emoji": True},
                    "value": "syukkin",
                    "action_id": "button_syukkin-action",
                },
            }
        ],
    )

    date: str = f"{datetime.now(JST_).day}日"
    results: Dict[str, str] = notion.get_pages_from_database(database_id)
    titles: List[str] = [result["properties"]["Name"]["title"][0]["plain_text"] for result in results]

    if date not in titles:
        notion.create_page(database_id=database_id, title=date)
    else:
        logger.warning("Todays record is alredy existed.")


def syukkin_button(body, client, logger):
    logger.info(body)
    if body["user"]["id"] != os.environ.get("USER_ID"):
        logger.warning(f"{body['user']['id']} try to push the button.")
        return BoltResponse(status=200)

    channel: str = body["channel"]["id"]
    ts: str = body["message"]["ts"]

    syukkin_time: str = datetime.now(JST).strftime("%m/%d %H:%M")

    client.chat_postMessage(channel=channel, thread_ts=ts, text=f"[出勤] {syukkin_time}")

    client.chat_update(
        channel=channel,
        ts=ts,
        text="yahho-",
        blocks=[
            {
                "type": "section",
                "block_id": syukkin_time,
                "text": {"type": "mrkdwn", "text": "おつおつ。"},
                "accessory": {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "退勤", "emoji": True},
                    "value": "taikin",
                    "action_id": "button_taikin-action",
                },
            }
        ],
    )
    client.users_profile_set(
        token=os.environ.get("SLACK_USER_TOKEN"),
        profile={
            "status_text": "作業ちう",
            "status_emoji": ":hamster:",
        },
    )


def taikin_button(body, client, logger):
    logger.info(body)
    if body["user"]["id"] != os.environ.get("USER_ID"):
        logger.warning(f"{body['user']['id']} try to push the button.")
        return BoltResponse(status=200)

    channel: str = body["channel"]["id"]
    ts: str = body["message"]["ts"]

    syukkin_time: datetime = datetime.strptime(body["actions"][0]["block_id"], "%m/%d %H:%M")
    taikin_time: datetime = datetime.strptime(datetime.now(JST).strftime("%m/%d %H:%M"), "%m/%d %H:%M")
    kinmu_time: int = (taikin_time - syukkin_time).seconds

    client.chat_postMessage(channel=channel, thread_ts=ts, text=f"[退勤] {taikin_time.strftime('%m/%d %H:%M')}")

    client.chat_update(
        channel=channel,
        ts=ts,
        text="yahho-",
        blocks=[
            {
                "type": "section",
                "block_id": "taikin",
                "text": {"type": "mrkdwn", "text": "お疲れ様やな。"},
                "accessory": {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "出勤", "emoji": True},
                    "value": "syukkin",
                    "action_id": "button_syukkin-action",
                },
            }
        ],
    )
    client.users_profile_set(
        token=os.environ.get("SLACK_USER_TOKEN"),
        profile={
            "status_text": "",
            "status_emoji": "",
        },
    )

    date: str = f"{datetime.now(JST).day}日"
    results: Dict = notion.get_pages_from_database(database_id)
    ids: Dict[str:str] = {result["properties"]["Name"]["title"][0]["plain_text"]: result["id"] for result in results}
    notion.update_time_property(ids[date], kinmu_time // 60)


def message(body, message, client, logger):
    logger.info(body)
    if body["event"]["user"] != os.environ.get("USER_ID"):
        logger.warning(f"{body['event']['user']} try to send messages.")
        return BoltResponse(status=200)

    channel: str = body["event"]["channel"]
    ts: str = body["event"]["ts"]

    date: str = f"{datetime.now(JST).day}日"
    results: Dict = notion.get_pages_from_database(database_id)
    ids: Dict[str:str] = {result["properties"]["Name"]["title"][0]["plain_text"]: result["id"] for result in results}

    tags = []
    texts = []
    temp_test = []
    for i in message["text"].split("\n"):
        if i.startswith("[") and i.endswith("]"):
            tags.append(i[1:-1])
            if temp_test:
                texts.append("\n".join(temp_test))
                temp_test = []
        else:
            temp_test.append(i)
    else:
        texts.append("\n".join(temp_test))

    progress: Dict[str, str] = {k: v for k, v in zip(tags, texts)}

    notion.update_tags_property(ids[date], tags)
    notion.add_progress(ids[date], progress)

    client.reactions_add(
        channel=channel,
        timestamp=ts,
        name="thumbsup",
    )


def arc_func(ack):
    ack()


app.event("app_mention")(ack=arc_func, lazy=[push_button])
app.action("button_syukkin-action")(ack=arc_func, lazy=[syukkin_button])
app.action("button_taikin-action")(ack=arc_func, lazy=[taikin_button])
app.message(re.compile(r"^[[]"))(ack=arc_func, lazy=[message])
