import datetime
import time
import random

import requests
from bs4 import BeautifulSoup
import IPy

import event
import debug


class Scrapper(event.Subject):

    def __init__(self, min_delay=334, max_delay=500, timeout=3.03):
        super().__init__()

        self.min_delay = min_delay
        self.max_delay = max_delay
        self.previous_tick_time = datetime.datetime.now() - datetime.timedelta(milliseconds=self.max_delay)
        self.next_delay = 0
        self.timeout = timeout

        self.max_connect_timeout = 3
        self.connect_timeout_counter = 0
        self.max_read_timeout = 3
        self.read_timeout_counter = 0
        self.max_connection_error = 3
        self.connection_error_counter = 0
        self.max_chunked_encoding_error = 3
        self.chunked_encoding_error_counter = 0

    @property
    def min_delay(self):
        return self.__min_delay

    @min_delay.setter
    def min_delay(self, min_delay):
        if min_delay > 0:
            self.__min_delay = min_delay
        else:
            self.__min_delay = 1

    @property
    def max_delay(self):
        return self.__max_delay

    @max_delay.setter
    def max_delay(self, max_delay):
        if max_delay > self.min_delay:
            self.__max_delay = max_delay
        else:
            self.__max_delay = self.min_delay + 1

    @property
    def timeout(self):
        return self.__timeout

    @timeout.setter
    def timeout(self, timeout):
        if timeout <= 0.0:
            self.__timeout = 0.0
        else:
            self.__timeout = timeout

    @property
    def max_connect_timeout(self):
        return self.__max_connect_timeout

    @max_connect_timeout.setter
    def max_connect_timeout(self, max_connect_timeout):
        if max_connect_timeout < 0.1:
            self.__max_connect_timeout = 0.1
        else:
            self.__max_connect_timeout = max_connect_timeout

    @property
    def max_read_timeout(self):
        return self.__max_read_timeout

    @max_read_timeout.setter
    def max_read_timeout(self, max_read_timeout):
        if max_read_timeout < 1:
            self.__max_read_timeout = 1
        else:
            self.__max_read_timeout = max_read_timeout

    @property
    def max_connection_error(self):
        return self.__max_connection_error

    @max_connection_error.setter
    def max_connection_error(self, max_connection_error):
        if max_connection_error < 1:
            self.__max_connection_error = 1
        else:
            self.__max_connection_error = max_connection_error

    @property
    def max_chunked_encoding_error(self):
        return self.__max_chunked_encoding_error

    @max_chunked_encoding_error.setter
    def max_chunked_encoding_error(self, max_chunked_encoding_error):
        if max_chunked_encoding_error < 1:
            self.__max_chunked_encoding_error = 1
        else:
            self.__max_chunked_encoding_error = max_chunked_encoding_error

    def scrape(self, url):
        self.delay()
        source = self.get_source(url)
        self.update_delay_times()

        return source

    def delay(self):
        elapsed_time = int(round((datetime.datetime.now().timestamp() - self.previous_tick_time.timestamp()) * 1000))

        if elapsed_time < self.next_delay:
            remaining_delay = self.next_delay - elapsed_time
            time.sleep(remaining_delay / 1000)

    def update_delay_times(self):
        self.previous_tick_time = datetime.datetime.now()
        self.next_delay = random.randint(self.min_delay, self.max_delay)

    def get_source(self, url):
        while True:
            try:
                with requests.get(url, timeout=self.timeout) as source:
                    source.encoding = 'utf-8'
                    self.reset_error_counters('connect_timeout_counter', 'read_timeout_counter',
                                              'connection_error_counter', 'chunked_encoding_error_counter')
                    return BeautifulSoup(source.text, features="html.parser")
            except requests.exceptions.ConnectTimeout:
                self.handle_connect_timeout()
            except requests.ReadTimeout:
                self.handle_read_timeout()
            except requests.exceptions.SSLError:
                self.handle_ssl_error(url)
            except requests.ConnectionError:
                self.handle_connection_error()
            except requests.exceptions.ChunkedEncodingError:
                self.handle_chunked_encoding_error()
            except requests.exceptions.RequestException as e:
                raise NormalScrapingException(f'Undefined requests error: {str(e)}')

    def handle_connect_timeout(self):
        self.connect_timeout_counter += 1
        self.connect_timeout(f'{self.connect_timeout_counter}/{self.max_connect_timeout}')

        if self.connect_timeout_counter >= self.max_connect_timeout:
            self.reset_error_counters('connect_timeout_counter')
            raise ConnectTimeout()

    def handle_read_timeout(self):
        self.read_timeout_counter += 1
        self.connect_timeout(f'{self.read_timeout_counter}/{self.max_read_timeout}')

        if self.read_timeout_counter >= self.max_read_timeout:
            self.reset_error_counters('read_timeout_counter')
            raise ReadTimeout()

    def handle_ssl_error(self, url):
        raise SSLError(url)

    def handle_connection_error(self):
        self.connection_error_counter += 1
        self.connection_error(f'{self.connection_error_counter}/{self.max_connection_error}')

        if self.connection_error_counter >= self.max_connection_error:
            self.reset_error_counters('connection_error_counter')
            raise ConnectionErrorOccurred()

    def handle_chunked_encoding_error(self):
        self.chunked_encoding_error_counter += 1
        self.chunked_encoding_error(f'{self.chunked_encoding_error_counter}/{self.max_chunked_encoding_error}')

        if self.connection_error_counter >= self.max_connection_error:
            self.reset_error_counters('chunked_encoding_error_counter')
            raise ChunkedEncodingError()

    def reset_error_counters(self, *args):
        for counter_name in args:
            try:
                self.__getattribute__(counter_name)
            except AttributeError as e:
                raise e
            else:
                self.__setattr__(counter_name, 0)

    @event.signal
    def connect_timeout(self, timeout_info):
        pass

    @event.signal
    def read_timeout(self, timeout_info):
        pass

    @event.signal
    def connection_error(self, error_info):
        pass

    @event.signal
    def chunked_encoding_error(self, error_info):
        pass


class StealthScrapper(Scrapper):
    PROXY_URL = 'https://free-proxy-list.net/'
    PROXY_FILE_DIR = r'files/proxy.txt'
    USER_AGENTS_FILE_DIR = r'files/user_agents.txt'
    WRONG_INDEX = -1

    def __init__(self, min_delay=334, max_delay=500, timeout=3.03, proxy_from_file=False):
        super().__init__(min_delay, max_delay, timeout)

        self.proxy_from_file = proxy_from_file
        self.used_proxy_index = StealthScrapper.WRONG_INDEX
        self.proxy = []
        self.used_user_agent_index = StealthScrapper.WRONG_INDEX
        self.user_agents = []
        self.max_proxy_ssl_error = 5
        self.proxy_ssl_error_counter = 0
        self.change_stealth = True

    @property
    def max_proxy_ssl_error(self):
        return self.__max_proxy_ssl_error

    @max_proxy_ssl_error.setter
    def max_proxy_ssl_error(self, max_proxy_ssl_error):
        if max_proxy_ssl_error < 1:
            self.__max_proxy_ssl_error = 1
        else:
            self.__max_proxy_ssl_error = max_proxy_ssl_error

    def scrape(self, url):
        self.renew_stealth()

        protocol = url[0:url.find(':')]
        session = requests.Session()
        self.prepare_stealth_session(session, protocol)

        self.delay()
        source = self.get_source(url, session, protocol)
        self.update_delay_times()

        return source

    def renew_stealth(self):
        if len(self.proxy) == 0:
            self.refresh_proxy()
        if len(self.user_agents) == 0:
            self.refresh_user_agents()

    def refresh_stealth(self):
        self.refresh_proxy()
        self.refresh_user_agents()

    def refresh_proxy(self):
        self.used_proxy_index = StealthScrapper.WRONG_INDEX
        self.provide_proxy()

    def refresh_user_agents(self):
        self.used_user_agent_index = StealthScrapper.WRONG_INDEX
        self.provide_user_agents()

    def provide_proxy(self):
        if self.proxy_from_file:
            self.provide_proxy_from_file()
        else:
            self.provide_proxy_from_web()

    def provide_proxy_from_file(self):
        self.proxy.clear()

        with open(StealthScrapper.PROXY_FILE_DIR, 'r') as proxy_file:
            for line in proxy_file.read().splitlines():
                proxy_data = line.split(';')
                protocol = proxy_data[0]
                ip = proxy_data[1]
                port = proxy_data[2]

                if Proxy.is_valid(protocol, ip, int(port)):
                    self.proxy.append(Proxy(protocol, ip, int(port)))

    def provide_proxy_from_web(self):
        self.proxy.clear()
        proxy_source = Scrapper.scrape(super(), StealthScrapper.PROXY_URL)

        try:
            self.extract_proxy_from_source(proxy_source)
        except Exception as e:
            raise ProxyScrapingError(debug.debug_info(repr(e)))

        if len(self.proxy) == 0:
            raise ProxyScrapingError(debug.debug_info('Proxy list is empty'))

    def extract_proxy_from_source(self, proxy_source):
        for item in proxy_source.select('tbody tr'):
            if len(item.select('td')) > 6:
                ip = item.select('td')[0].text
                port = item.select('td')[1].text
                protocol = Proxy.HTTP if item.select('td')[6].text == 'no' else Proxy.HTTPS

                if Proxy.is_valid(protocol, ip, int(port)):
                    self.proxy.append(Proxy(protocol, ip, int(port)))

    def provide_user_agents(self):
        self.user_agents.clear()

        with open(StealthScrapper.USER_AGENTS_FILE_DIR, 'r') as user_agents_file:
            for line in user_agents_file.read().splitlines():
                self.user_agents.append(line)

    def prepare_stealth_session(self, session, protocol):
        if self.change_stealth or self.stealth_change_required():
            self.draw_proxy(protocol)
            self.draw_user_agent()

        session.proxies = {self.proxy[self.used_proxy_index].protocol: self.proxy[self.used_proxy_index].address()}
        session.headers = {'User-Agent': self.user_agents[self.used_user_agent_index]}

    def stealth_change_required(self):
        return self.used_proxy_index == StealthScrapper.WRONG_INDEX or \
               self.used_user_agent_index == StealthScrapper.WRONG_INDEX

    def draw_proxy(self, protocol):
        protocol_proxy_indexes = [i for i, x in enumerate(self.proxy) if x.protocol == protocol]

        if len(protocol_proxy_indexes) == 0:
            raise LackOfProxy(protocol)
        elif len(protocol_proxy_indexes) == 1:
            self.used_proxy_index = protocol_proxy_indexes[0]
        else:
            previous_proxy_index = self.used_proxy_index
            while self.used_proxy_index == previous_proxy_index:
                self.used_proxy_index = random.choice(protocol_proxy_indexes)

        return {self.proxy[self.used_proxy_index].protocol: self.proxy[self.used_proxy_index].address()}

    def draw_user_agent(self):
        if len(self.user_agents) == 0:
            raise LackOfUserAgents()
        elif len(self.user_agents) == 1:
            self.used_user_agent_index = 0
        else:
            previous_user_agent_index = self.used_user_agent_index
            while self.used_user_agent_index == previous_user_agent_index:
                self.used_user_agent_index = random.randint(0, len(self.user_agents)-1)

        return {'User-Agent': self.user_agents[self.used_user_agent_index]}

    def get_source(self, url, session, protocol):
        while True:
            try:
                with session.get(url, timeout=self.timeout) as source:
                    source.encoding = 'utf-8'
                    self.reset_error_counters('connect_timeout_counter', 'read_timeout_counter',
                                              'connection_error_counter', 'proxy_ssl_error_counter',
                                              'chunked_encoding_error_counter')
                    return BeautifulSoup(source.text, features="html.parser")
            except requests.exceptions.ConnectTimeout:
                self.handle_connect_timeout(session, protocol)
            except requests.exceptions.ProxyError:
                self.handle_proxy_error(session, protocol)
            except requests.exceptions.InvalidHeader:
                self.handle_invalid_header(session)
            except requests.ReadTimeout:
                self.handle_read_timeout(session, protocol)
            except requests.exceptions.SSLError:
                self.handle_ssl_error(url, session, protocol)
            except requests.exceptions.ConnectionError:
                self.handle_connection_error(session, protocol)
            except requests.exceptions.ChunkedEncodingError:
                self.handle_chunked_encoding_error(session, protocol)
            except requests.exceptions.RequestException as e:
                raise StealthScrapingException(f'Undefined requests error: {str(e)}')

    def handle_connect_timeout(self, session, protocol):
        self.connect_timeout_counter += 1
        self.proxy_connect_timeout(f'{str(self.proxy[self.used_proxy_index])} '
                                   f'{self.connect_timeout_counter}/{self.max_connect_timeout}')

        if self.connect_timeout_counter >= self.max_connect_timeout:
            self.reset_error_counters('connect_timeout_counter', 'read_timeout_counter', 'connection_error_counter',
                                      'proxy_ssl_error_counter', 'chunked_encoding_error_counter')
            self.remove_proxy(self.used_proxy_index, protocol)
            session.proxies = self.draw_proxy(protocol)

    def handle_proxy_error(self, session, protocol):
        self.proxy_error(str(self.proxy[self.used_proxy_index]))
        self.remove_proxy(self.used_proxy_index, protocol)
        self.reset_error_counters('connect_timeout_counter', 'read_timeout_counter', 'connection_error_counter',
                                  'proxy_ssl_error_counter', 'chunked_encoding_error_counter')
        session.proxies = self.draw_proxy(protocol)

    def handle_invalid_header(self, session):
        self.invalid_user_agent(self.user_agents[self.used_user_agent_index])
        self.remove_user_agent(self.used_user_agent_index)
        self.reset_error_counters('connect_timeout_counter', 'read_timeout_counter', 'connection_error_counter',
                                  'proxy_ssl_error_counter', 'chunked_encoding_error_counter')
        session.headers = self.draw_user_agent()

    def handle_read_timeout(self, session, protocol):
        self.read_timeout_counter += 1
        self.proxy_read_timeout(f'{self.read_timeout_counter}/{self.max_read_timeout}')

        if self.read_timeout_counter >= self.max_read_timeout:
            self.reset_error_counters('connect_timeout_counter', 'read_timeout_counter', 'connection_error_counter',
                                      'proxy_ssl_error_counter', 'chunked_encoding_error_counter')
            raise ProxyReadTimeout()

        self.reset_error_counters('connect_timeout_counter', 'connection_error_counter', 'proxy_ssl_error_counter',
                                  'chunked_encoding_error_counter')
        self.remove_proxy(self.used_proxy_index, protocol)
        session.proxies = self.draw_proxy(protocol)

    def handle_ssl_error(self, url, session, protocol):
        self.proxy_ssl_error_counter += 1
        self.proxy_ssl_error(f'{str(self.proxy[self.used_proxy_index])} {self.proxy_ssl_error_counter}/'
                             f'{self.max_proxy_ssl_error}', url)

        if self.proxy_ssl_error_counter >= self.max_proxy_ssl_error:
            self.reset_error_counters('connect_timeout_counter', 'read_timeout_counter', 'connection_error_counter',
                                      'proxy_ssl_error_counter', 'chunked_encoding_error_counter')
            raise ProxySSLError()

        self.reset_error_counters('connect_timeout_counter', 'read_timeout_counter', 'connection_error_counter',
                                  'chunked_encoding_error_counter')
        self.remove_proxy(self.used_proxy_index, protocol)
        session.proxies = self.draw_proxy(protocol)

    def handle_connection_error(self, session, protocol):
        self.connection_error_counter += 1
        self.proxy_connection_error(f'{self.connection_error_counter}/{self.max_connection_error}')

        if self.connection_error_counter >= self.max_connection_error:
            self.reset_error_counters('connect_timeout_counter', 'read_timeout_counter', 'connection_error_counter',
                                      'proxy_ssl_error_counter', 'chunked_encoding_error_counter')
            raise ProxyConnectionError()

        self.reset_error_counters('connect_timeout_counter', 'read_timeout_counter', 'proxy_ssl_error_counter',
                                  'chunked_encoding_error_counter')
        self.remove_proxy(self.used_proxy_index, protocol)
        session.proxies = self.draw_proxy(protocol)

    def handle_chunked_encoding_error(self, session, protocol):
        self.chunked_encoding_error_counter += 1
        self.proxy_chunked_encoding_error(f'{self.chunked_encoding_error_counter}/{self.max_chunked_encoding_error}')

        if self.chunked_encoding_error_counter >= self.max_chunked_encoding_error:
            self.reset_error_counters('connect_timeout_counter', 'read_timeout_counter', 'connection_error_counter',
                                      'proxy_ssl_error_counter', 'chunked_encoding_error_counter')
            raise ProxyChunkedEncodingError()

        self.reset_error_counters('connect_timeout_counter', 'read_timeout_counter', 'proxy_ssl_error_counter',
                                  'connection_error_counter')
        session.proxies = self.draw_proxy(protocol)

    def remove_proxy(self, index, protocol):
        del self.proxy[index]

        if index == self.used_proxy_index:
            self.used_proxy_index = StealthScrapper.WRONG_INDEX

        if len([proxy for proxy in self.proxy if proxy.protocol == protocol]) == 0:
            self.proxy_exhausted(protocol)

    def remove_user_agent(self, index):
        del self.user_agents[index]

        if index == self.used_user_agent_index:
            self.used_user_agent_index = StealthScrapper.WRONG_INDEX

        if len(self.user_agents) == 0:
            self.user_agents_exhausted()

    @event.signal
    def proxy_connect_timeout(self, proxy_info):
        pass

    @event.signal
    def proxy_error(self, proxy_info):
        pass

    @event.signal
    def invalid_user_agent(self, user_agent_info):
        pass

    @event.signal
    def proxy_read_timeout(self, info):
        pass

    @event.signal
    def proxy_ssl_error(self, proxy_info, url):
        pass

    @event.signal
    def proxy_connection_error(self, info):
        pass

    @event.signal
    def proxy_chunked_encoding_error(self, info):
        pass

    @event.signal
    def proxy_exhausted(self, protocol):
        pass

    @event.signal
    def user_agents_exhausted(self):
        pass


class Proxy:
    HTTP = 'http'
    HTTPS = 'https'
    MIN_PORT = 0
    MAX_PORT = 65535

    def __init__(self, protocol, ip, port):
        self.protocol = protocol
        self.ip = ip
        self.port = port

    def __repr__(self):
        return f'{self.protocol}://{self.ip}:{self.port}'

    def __str__(self):
        return f'{self.protocol}://{self.ip}:{self.port}'

    def address(self):
        return f'{self.protocol}://{self.ip}:{self.port}'

    @staticmethod
    def is_valid(protocol, ip, port):
        if Proxy.protocol_valid(protocol) and Proxy.ip_valid(ip) and Proxy.port_valid(port):
            return True
        return False

    @staticmethod
    def protocol_valid(protocol):
        if protocol in (Proxy.HTTP, Proxy.HTTPS):
            return True
        return False

    @staticmethod
    def ip_valid(ip):
        try:
            IPy.IP(ip)
            return True
        except ValueError:
            return False

    @staticmethod
    def port_valid(port):
        if Proxy.MIN_PORT <= port <= Proxy.MAX_PORT:
            return True
        return False


class ScrapingException(Exception):
    pass


class NormalScrapingException(ScrapingException):
    pass


class StealthScrapingException(ScrapingException):
    pass


class ConnectTimeout(NormalScrapingException):
    pass


class ReadTimeout(NormalScrapingException):
    pass


class ConnectionErrorOccurred(NormalScrapingException):
    pass


class ChunkedEncodingError(NormalScrapingException):
    pass


class SSLError(NormalScrapingException):
    pass


class ProxyReadTimeout(StealthScrapingException):
    pass


class ProxySSLError(StealthScrapingException):
    pass


class ProxyConnectionError(StealthScrapingException):
    pass


class ProxyChunkedEncodingError(StealthScrapingException):
    pass


class LackOfProxy(StealthScrapingException):
    pass


class LackOfUserAgents(StealthScrapingException):
    pass


class ProxyScrapingError(StealthScrapingException):
    pass
