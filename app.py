import twitter
import ccxt
import logging
import wget
import pytesseract
from datetime import datetime, timedelta, timezone
from dynaconf import settings
from PIL import Image

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)-40s %(levelname)-8s %(message)s")
logger = logging.getLogger(__name__)

bittrex = ccxt.bittrex()

coin_keywords = ['coin', 'week']

api = twitter.Api(consumer_key=settings.TWITTER.CONSUMER_KEY,
                  consumer_secret=settings.TWITTER.CONSUMER_SECRET,
                  access_token_key=settings.TWITTER.ACCESS_TOKEN,
                  access_token_secret=settings.TWITTER.ACCESS_TOKEN_SECRET)


def extract_coin(text):
    # Extract all possible coins
    possible_coins = []
    for word in text.split(" "):
        if len(word) == 3 or len(word) == 4:
            possible_coins.append(word)

    if len(possible_coins) == 0:
        logger.info("Nop it was not a coin of the week: {}".format(text))
        return None

    # Try to find real coin
    found_coin = None
    for coin in possible_coins:
        symbol = "{}/ETH".format(coin)

        try:
            bittrex.fetch_ticker(symbol)
        except:
            logging.debug("{} is not a coin".format(coin))
            continue

        found_coin = coin

    return found_coin


def main():
    statuses = api.GetUserTimeline(screen_name='officialmcafee')

    last_hour = datetime.now(timezone.utc) - timedelta(hours=1)
    for status in statuses:
        # Only fetch the last hour
        created = datetime.strptime(status.created_at, "%a %b %d %H:%M:%S %z %Y")
        if created < last_hour:
            continue

        print(status)

        # Check if relevant
        keywords = [x for x in coin_keywords if x in status.text.lower()]
        if len(keywords) != len(coin_keywords):
            continue

        logger.info("Seems like a coin of the week, trying to find it")

        # Extract all possible coins from text
        found_coin = extract_coin(status.text)

        if found_coin is not None:
            logger.info("Found the coin of the week: {}".format(found_coin))
            break

        logger.info("Did not find a coin the the text")

        # Extract all possible coins from image
        if len(status.media) == 0:
            logger.info("No media to OCR, no coin to be found")
            continue

        url = status.media[0].media_url
        filename = wget.download(url, "./data/")
        image_text = pytesseract.image_to_string(Image.open(filename))

        found_coin = extract_coin(image_text)

        if found_coin is not None:
            logger.info("Found the coin of the week: {}".format(found_coin))
            break

if __name__ == '__main__':
    main()
