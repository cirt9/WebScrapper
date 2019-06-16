import logging
import datetime

import scrapping
import event


class ScrapperLogger:
    LOGS_DIRECTORY = r'logs/'

    def __init__(self):
        self.log_filename = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S') + '.log'
        self.logger = logging.getLogger('ScrapperLogger')
        self.logger.setLevel(logging.INFO)

        file_handler = logging.FileHandler(filename=f'{ScrapperLogger.LOGS_DIRECTORY}{self.log_filename}')
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)

    def log(self, msg, level=logging.INFO):
        self.logger.log(level, msg)

    def on_stealth_mode_changed(self, state):
        self.logger.info(f'Stealth mode state was changed to: {state}')

    def on_proxy_connect_timeout(self, proxy_info):
        self.logger.info(f'Proxy connection timeout: {proxy_info}')

    def on_proxy_error(self, proxy_info):
        self.logger.warning(f'Proxy error: {proxy_info}')

    def on_invalid_user_agent(self, user_agent_info):
        self.logger.info(f'Invalid user agent: {user_agent_info}')

    def on_read_failure(self, info):
        self.logger.warning(f'Read failure: {info}')

    def on_lack_of_proxy(self, protocol):
        self.logger.warning(f'Lack of proxy of {protocol} protocol')

    def on_proxy_exhausted(self):
        self.logger.warning('Proxy exhausted')

    def on_lack_of_user_agent(self):
        self.logger.warning('Lack of user agent')

    def on_user_agents_exhausted(self):
        self.logger.warning('User agents exhausted')


def main():
    url = 'https://www.google.com/'

    scrapper = scrapping.Scrapper()
    logger = ScrapperLogger()

    event.connect(scrapper, scrapper.stealth_mode_changed, logger.on_stealth_mode_changed)
    event.connect(scrapper, scrapper.proxy_connect_timeout, logger.on_proxy_connect_timeout)
    event.connect(scrapper, scrapper.proxy_error, logger.on_proxy_error)
    event.connect(scrapper, scrapper.invalid_user_agent, logger.on_invalid_user_agent)
    event.connect(scrapper, scrapper.read_failure, logger.on_read_failure)

    event.connect(scrapper, scrapper.lack_of_proxy, logger.on_lack_of_proxy)
    event.connect(scrapper, scrapper.proxy_exhausted, logger.on_proxy_exhausted)
    event.connect(scrapper, scrapper.lack_of_user_agent, logger.on_lack_of_user_agent)
    event.connect(scrapper, scrapper.user_agents_exhausted, logger.on_user_agents_exhausted)

    scrapper.enable_stealth_mode()

    try:
        soup = scrapper.scrape(url)
        print(soup)
    except scrapping.requests.ConnectTimeout as exception:
        logger.log(f'Non proxy connect timeout: {type(exception).__name__}', logging.CRITICAL)
    except scrapping.requests.ReadTimeout as exception:
        logger.log(f'Read error, max failure exceeded: {type(exception).__name__}', logging.CRITICAL)
    except scrapping.requests.ConnectionError as exception:
        logger.log(type(exception).__name__, logging.CRITICAL)
    except scrapping.requests.exceptions.RequestException as exception:
        logger.log(f'Undefined requests error: {type(exception).__name__}', logging.CRITICAL)


if __name__ == '__main__':
    main()
