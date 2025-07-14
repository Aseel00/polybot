import flask
from flask import request
import os
from polybot.bot import Bot, QuoteBot, ImageProcessingBot
from polybot.dynamo_storage import DynamoDBStorage
import boto3
import json

def load_secrets(secret_name, region):
    client = boto3.client("secretsmanager", region_name=region)
    response = client.get_secret_value(SecretId=secret_name)
    secret = response["SecretString"]
    return json.loads(secret)

# Load secrets from AWS Secrets Manager
region = os.getenv("REGION", "eu-north-1")  # fallback if not passed
secrets = load_secrets("polybot-dev", region)

TELEGRAM_BOT_TOKEN = secrets['TELEGRAM_BOT_TOKEN']
BOT_APP_URL = secrets['BOT_APP_URL']
YOLO_URL = secrets['YOLO_URL']
BUCKET_NAME = secrets['BUCKET_NAME']
REGION = secrets['REGION']
polybot_env = secrets['POLYBOT_ENV']
TABLE_NAME = secrets["DDB_TABLE_NAME"]
SQS_URL =secrets["SQS_URL"]

app = flask.Flask(__name__)



dynamo_storage = DynamoDBStorage(table_name=TABLE_NAME, region=REGION)

@app.route('/', methods=['GET'])
def index():
    return 'Ok'


@app.route(f'/{TELEGRAM_BOT_TOKEN}/', methods=['POST'])
def webhook():
    req = request.get_json()
    bot.handle_message(req['message'])
    return 'Ok'

@app.route("/predictions/<prediction_id>", methods=["POST"])
def receive_prediction(prediction_id):
    try:
        data = request.get_json()
        chat_id = data.get("chat_id")
        print("📨 Callback received:", data)
        if not chat_id:
            return "Missing chat_id", 400

        # Use the shared DynamoDBStorage to get data
        prediction = dynamo_storage.get_prediction_by_uid(prediction_id)
        if not prediction:
            return "Prediction not found", 404

        print("📦 Prediction objects:", prediction["detection_objects"])

        labels = [obj["label"] for obj in prediction["detection_objects"]]
        label_text = "Detected: " + ", ".join(labels) if labels else "No objects detected."
        bot.send_text(chat_id, label_text)

        return "ok"
    except Exception as e:
        return f"Error: {str(e)}", 500

if __name__ == "__main__":
    #bot = Bot(TELEGRAM_BOT_TOKEN, TELEGRAM_APP_URL)
    #bot = Bot(TELEGRAM_BOT_TOKEN, BOT_APP_URL)
    #bot = QuoteBot(TELEGRAM_BOT_TOKEN, BOT_APP_URL)
    bot = ImageProcessingBot(TELEGRAM_BOT_TOKEN, BOT_APP_URL,SQS_URL,polybot_env,BUCKET_NAME,REGION,YOLO_URL)

    app.run(host='0.0.0.0', port=8443)
