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

    def on_connect_timeout(self, timeout_info):
        self.logger.warning(f'Connect timeout: {timeout_info}')

    def on_read_timeout(self, timeout_info):
        self.logger.warning(f'Read timeout: {timeout_info}')

    def on_connection_error(self, error_info):
        self.logger.warning(f'Connection error: {error_info}')

    def on_proxy_connect_timeout(self, proxy_info):
        self.logger.warning(f'Proxy connect timeout: {proxy_info}')

    def on_proxy_error(self, proxy_info):
        self.logger.warning(f'Proxy error: {proxy_info}')

    def on_invalid_user_agent(self, user_agent_info):
        self.logger.warning(f'Invalid user agent: {user_agent_info}')

    def on_proxy_read_timeout(self, info):
        self.logger.warning(f'Proxy read timeout: {info}')

    def on_proxy_ssl_error(self, proxy_info, url):
        self.logger.warning(f'Proxy SSL error: {proxy_info}, url: {url}')

    def on_proxy_connection_error(self, info):
        self.logger.warning(f'Proxy connection error: {info}')

    def on_proxy_exhausted(self):
        self.logger.warning('Proxy exhausted')

    def on_user_agents_exhausted(self):
        self.logger.warning('User agents exhausted')


def main():
    scrapper = scrapping.StealthScrapper()
    logger = ScrapperLogger()

    event.connect(scrapper, scrapper.connect_timeout, logger.on_connect_timeout)
    event.connect(scrapper, scrapper.read_timeout, logger.on_read_timeout)
    event.connect(scrapper, scrapper.connection_error, logger.on_connection_error)

    event.connect(scrapper, scrapper.proxy_connect_timeout, logger.on_proxy_connect_timeout)
    event.connect(scrapper, scrapper.proxy_error, logger.on_proxy_error)
    event.connect(scrapper, scrapper.invalid_user_agent, logger.on_invalid_user_agent)
    event.connect(scrapper, scrapper.proxy_read_timeout, logger.on_proxy_read_timeout)
    event.connect(scrapper, scrapper.proxy_ssl_error, logger.on_proxy_ssl_error)
    event.connect(scrapper, scrapper.proxy_connection_error, logger.on_proxy_connection_error)
    event.connect(scrapper, scrapper.proxy_exhausted, logger.on_proxy_exhausted)
    event.connect(scrapper, scrapper.user_agents_exhausted, logger.on_user_agents_exhausted)

    try:
        source = scrapper.scrape(r'https://www.google.com/')
        print(source)
    except scrapping.ScrappingException as exception:
        logger.log(f'Exception: {type(exception).__name__} ({str(exception)})', logging.CRITICAL)


if __name__ == '__main__':
    main()
