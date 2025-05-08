import telebot
from loguru import logger
import os
import time
from telebot.types import InputFile
from polybot.img_proc import Img


class Bot:

    def __init__(self, token, telegram_chat_url):
        # create a new instance of the TeleBot class.
        # all communication with Telegram servers are done using self.telegram_bot_client
        self.telegram_bot_client = telebot.TeleBot(token)

        # remove any existing webhooks configured in Telegram servers
        self.telegram_bot_client.remove_webhook()
        time.sleep(0.5)

        # set the webhook URL
        self.telegram_bot_client.set_webhook(url=f'{telegram_chat_url}/{token}/', timeout=60)

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
    def __init__(self, token,telegram_chat_url ):
        super().__init__(token, telegram_chat_url)
        self.concat_sessions = {}  # Store chat_id -> first image path

    def handle_message(self, msg):
        try:
            logger.info(f'Incoming message: {msg}')
            chat_id = msg['chat']['id']
            if 'text' in msg:
                text = msg['text'].strip().lower()
                if text == '/start' or True:  # Respond to any text
                    self.send_text(chat_id, "Hi, how can I help you?")
                    return
            if 'photo' in msg:
                caption = msg.get("caption", "").strip().lower()
                photo_path = self.download_user_photo(msg)
                if caption == "detect":
                    try:
                        import requests

                        # Send image to YOLO API
                        yolo_api_url = "http://localhost:8080/predict"  # Change if needed
                        with open(photo_path, "rb") as f:
                            files = {"file": (os.path.basename(photo_path), f, "image/jpeg")}
                            response = requests.post(yolo_api_url, files=files)
                        response.raise_for_status()
                        result = response.json()
                        labels = result.get("labels", [])
                        prediction_uid = result.get("prediction_uid")

                        if not prediction_uid:
                            self.send_text(chat_id, "Failed to get prediction UID.")
                            return

                        # Get annotated image
                        image_url = f"http://localhost:8080/prediction/{prediction_uid}/image"
                        image_response = requests.get(image_url, headers={"accept": "image/jpeg"})
                        image_response.raise_for_status()

                        # Send image and labels
                        label_list = " ".join(f" {label}" for label in labels) or "No objects detected."
                        #self.telegram_bot_client.send_photo(chat_id, image_response.content,
                         #                                   caption=f"Detected:\n{label_list}")
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
