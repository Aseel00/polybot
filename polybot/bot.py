import telebot
from loguru import logger
import os
import time
from telebot.types import InputFile
from polybot.img_proc import Img
import logging
import boto3
from botocore.exceptions import ClientError

class Bot:

    def __init__(self, token, telegram_chat_url):
        # create a new instance of the TeleBot class.
        # all communication with Telegram servers are done using self.telegram_bot_client
        self.telegram_bot_client = telebot.TeleBot(token)

        # remove any existing webhooks configured in Telegram servers
        self.telegram_bot_client.remove_webhook()
        time.sleep(0.5)

        # set the webhook URL
        #self.telegram_bot_client.set_webhook(url=f'{telegram_chat_url}/{token}/', timeout=60)
        crt_path = os.path.expandvars('$HOME/polybot/polybot.crt')
        self.telegram_bot_client.set_webhook(
            url=f'{telegram_chat_url}/{token}/',
            #certificate=open('$HOME/polybot/polybot.crt', 'r'),

            certificate=open(crt_path, 'r'),
            timeout=60
        )

        logger.info(f'Telegram Bot information\n\n{self.telegram_bot_client.get_me()}')

    def send_text(self, chat_id, text):
        self.telegram_bot_client.send_message(chat_id, text)

    def send_text_with_quote(self, chat_id, text, quoted_msg_id):
        self.telegram_bot_client.send_message(chat_id, text, reply_to_message_id=quoted_msg_id)

    def is_current_msg_photo(self, msg):
        return 'photo' in msg

    def download_user_photo(self, msg):
        """
        Downloads the photos that sent to the Bot to `photos` directory (should be existed)
        :return:
        """
        if not self.is_current_msg_photo(msg):
            raise RuntimeError(f'Message content of type \'photo\' expected')

        file_info = self.telegram_bot_client.get_file(msg['photo'][-1]['file_id'])
        data = self.telegram_bot_client.download_file(file_info.file_path)
        folder_name = file_info.file_path.split('/')[0]

        if not os.path.exists(folder_name):
            os.makedirs(folder_name)

        with open(file_info.file_path, 'wb') as photo:
            photo.write(data)

        return file_info.file_path

    def send_photo(self, chat_id, img_path):
        if not os.path.exists(img_path):
            raise RuntimeError("Image path doesn't exist")

        self.telegram_bot_client.send_photo(
            chat_id,
            InputFile(img_path)
        )

    def upload_file(self,file_name, bucket, region, object_name=None):
        """Upload a file to an S3 bucket

        :param region: The bucket region
        :param file_name: File to upload
        :param bucket: Bucket to upload to
        :param object_name: S3 object name. If not specified then file_name is used
        :return: True if file was uploaded, else False
        """

        # If S3 object_name was not specified, use file_name
        if object_name is None:
            object_name = os.path.basename(file_name)

        # Upload the file
        s3_client = boto3.client('s3',region)
        try:
            response = s3_client.upload_file(file_name, bucket, object_name)
        except ClientError as e:
            logging.error(e)
            return False
        return True
    def handle_message(self, msg):
        """Bot Main message handler"""
        logger.info(f'Incoming message: {msg}')
        self.send_text(msg['chat']['id'], f'Your original message: {msg["text"]}')


class QuoteBot(Bot):
    def handle_message(self, msg):
        logger.info(f'Incoming message: {msg}')

        if msg["text"] != 'Please don\'t quote me':
            self.send_text_with_quote(msg['chat']['id'], msg["text"], quoted_msg_id=msg["message_id"])


class ImageProcessingBot(Bot):
    def __init__(self, token,telegram_chat_url,s3_bucket="aseel-polybot-images",region="eu-north-1",yolo_url='localhost'):
        super().__init__(token, telegram_chat_url)
        self.yolo_url=yolo_url
        self.s3_bucket=s3_bucket
        self.region=region
        self.concat_sessions = {}  # Store chat_id -> first image path

    def handle_message(self, msg):
        try:
            logger.info(f'Incoming message: {msg}')
            chat_id = msg['chat']['id']
            if 'text' in msg:
                text = msg['text'].strip().lower()
                if text == '/start' or True:  # Respond to any text
                    self.send_text(chat_id, "Hi,Aseel")
                    return
            if 'photo' in msg:
                caption = msg.get("caption", "").strip().lower()
                photo_path = self.download_user_photo(msg)
                if caption == "detect":
                    try:
                        import requests
                        image_name = os.path.basename(photo_path)
                        uploaded = self.upload_file(photo_path, self.s3_bucket,self.region, image_name)
                        if not uploaded:
                            self.send_text(chat_id, "Failed to upload image to S3.")
                            return

                        yolo_api_url = f"http://{self.yolo_url}:8080/predict"
                        data={"image_name":image_name}
                        response = requests.post(yolo_api_url, data=data)

                        response.raise_for_status()
                        result = response.json()
                        labels = result.get("labels", [])


                        # Send image and labels
                        label_list = " ".join(f" {label}" for label in labels) or "No objects detected."

                        self.send_text(chat_id,label_list)

                    except Exception as e:
                        logger.error(f"YOLO detection error: {e}")
                        self.send_text(chat_id, "Object detection failed. Please try again.")
                    return

                valid_filters = {
                    'blur': 'blur',
                    'contour': 'contour',
                    'rotate': 'rotate',
                    'segment': 'segment',
                    'salt and pepper': 'salt_n_pepper',
                    'concat': 'concat'
                }

                # If user is in concat session, use the previous image and this one to concat
                if chat_id in self.concat_sessions and not caption:
                    first_photo_path = self.concat_sessions.pop(chat_id)
                    img1 = Img(first_photo_path)
                    img2 = Img(photo_path)
                    try:

                        img1.concat(img2, direction='horizontal')
                        filtered_img_path = img1.save_img()
                        self.send_photo(chat_id, filtered_img_path)
                    except RuntimeError as e:
                        self.send_text(chat_id, f"Concat failed: {e}")


                    return

                # Start concat session
                if caption == 'concat':
                    self.concat_sessions[chat_id] = photo_path

                    #self.send_text(chat_id, "Got the first photo for concatenation. Please send the second photo.")
                    return

                if not caption:
                    self.send_text(chat_id, "Please include a caption indicating the filter (e.g., 'blur').")
                    return

                if caption not in valid_filters:
                    self.send_text(chat_id,
                        "Unsupported filter. Please use one of: Blur, Contour, Rotate, Segment, Salt and pepper, Concat.")
                    return

                # Apply regular filters
                img = Img(photo_path)
                filter_method = getattr(img, valid_filters[caption])
                filter_method()
                filtered_img_path = img.save_img()
                self.send_photo(chat_id, filtered_img_path)

            else:
                self.send_text(chat_id, "Please send a photo with a caption indicating the filter.")

        except Exception as e:
            logger.error(f"Error processing image: {e}")
            self.send_text(msg['chat']['id'], "Something went wrong... please try again.")
