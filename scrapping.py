import datetime
import time
import random

import requests
from bs4 import BeautifulSoup

import event


class Scrapper(event.Subject):
    PROXY_URL = 'https://free-proxy-list.net/'
    PROXY_FILE_NAME = r'files/proxy.txt'
    USER_AGENTS_FILE_NAME = r'files/user_agents.txt'

    def __init__(self, min_delay=350, max_delay=1000, max_proxy_timeouts=3, max_read_failure=3, timeout=6.03):
        event.Subject.__init__(self)

        self.min_delay = min_delay
        self.max_delay = max_delay
        self.previous_tick_time = datetime.datetime.now() - datetime.timedelta(milliseconds=self.max_delay)
        self.next_delay = 0
        self.timeout = timeout
        self.stealth_mode = False
        self.used_proxy_index = -1
        self.proxy = []
        self.used_user_agent_index = -1
        self.user_agents = []
        self.max_proxy_timeouts = max_proxy_timeouts
        self.max_read_failure = max_read_failure
        self.read_failure_counter = 0

    @property
    def stealth_mode(self):
        return self.__stealth_mode

    @stealth_mode.setter
    def stealth_mode(self, state):
        self.__stealth_mode = state
        self.stealth_mode_changed(self.stealth_mode)

    def refresh_stealth(self):
        self.refresh_proxy()
        self.refresh_user_agents()

    def refresh_proxy(self):
        self.disable_stealth_mode()
        self.used_proxy_index = -1
        self.proxy = self.provide_proxy()
        self.enable_stealth_mode(False)

    def refresh_user_agents(self):
        self.used_user_agent_index = -1
        self.user_agents = self.provide_user_agents()

    def enable_stealth_mode(self, refresh_stealth=True):
        if not self.stealth_mode:
            self.stealth_mode = True

            if refresh_stealth:
                self.refresh_stealth()

    def disable_stealth_mode(self):
        if self.stealth_mode:
            self.stealth_mode = False

    def provide_proxy(self):
        try:
            proxy_list = self.provide_proxy_from_file()
        except FileNotFoundError:
            proxy_list = self.provide_proxy_from_web()

        return proxy_list

    def provide_proxy_from_file(self):
        proxy_list = []

        with open(Scrapper.PROXY_FILE_NAME, 'r') as proxy_file:
            for line in proxy_file.read().splitlines():
                proxy_data = line.split(';')
                proxy_list.append(Proxy(proxy_data[0], proxy_data[1]))

        return proxy_list

    def provide_proxy_from_web(self):
        proxy_list = []
        proxy_soup = self.scrape(self.PROXY_URL, False)

        for item in proxy_soup.select('tbody tr'):
            proxy = ':'.join([item.text for item in item.select('td')[:2]])
            protocol = 'http' if item.select('td')[6].text == 'no' else 'https'
            proxy_list.append(Proxy(protocol, proxy))

        return proxy_list

    def provide_user_agents(self):
        try:
            user_agents = self.provide_user_agents_from_file()
        except FileNotFoundError:
            raise RuntimeError('User agents file does not exist.')

        return user_agents

    def provide_user_agents_from_file(self):
        user_agents = []

        with open(Scrapper.USER_AGENTS_FILE_NAME, 'r') as user_agents_file:
            for line in user_agents_file.read().splitlines():
                user_agents.append(line)

        return user_agents

    def scrape(self, url, stealth_mode=None, switch_stealth=True):
        self.delay()

        stealth_mode = stealth_mode if stealth_mode is not None else self.stealth_mode
        protocol = url[0:url.find(':')]
        session = requests.Session()

        if stealth_mode:
            self.prepare_stealth(session, protocol, switch_stealth)

        source = self.get_source(url, session, protocol, stealth_mode)
        soup = BeautifulSoup(source.text, features="html.parser")
        self.update_delay_times()

        return soup

    def delay(self):
        elapsed_time = int(round((datetime.datetime.now().timestamp() - self.previous_tick_time.timestamp()) * 1000))

        if elapsed_time < self.next_delay:
            remaining_delay = self.next_delay - elapsed_time
            time.sleep(remaining_delay / 1000)

    def update_delay_times(self):
        self.previous_tick_time = datetime.datetime.now()
        self.next_delay = random.randint(self.min_delay, self.max_delay)

    def prepare_stealth(self, session, protocol, switch_stealth):
        if switch_stealth or not (self.used_proxy_index >= 0 and self.used_user_agent_index >= 0):
            self.draw_proxy(protocol)
            self.draw_user_agent()

        session.proxies = {self.proxy[self.used_proxy_index].protocol: self.proxy[self.used_proxy_index].address}
        session.headers = {'User-Agent': self.user_agents[self.used_user_agent_index]}

    def get_source(self, url, session, protocol, stealth_mode):
        while True:
            try:
                source = session.get(url, timeout=self.timeout)
                source.encoding = 'utf-8'
                self.reset_read_failure_counter()
                return source
            except requests.exceptions.ConnectTimeout as exception:
                if stealth_mode:
                    self.handle_connect_timeout(session, protocol)
                else:
                    raise exception
            except (requests.exceptions.ProxyError, requests.exceptions.SSLError):
                self.handle_proxy_error(session, protocol)
            except requests.exceptions.InvalidHeader:
                self.handle_invalid_header(session)
            except requests.ReadTimeout:
                self.handle_read_timeout()

    def draw_proxy(self, protocol):
        protocol_proxy_indexes = [i for i, x in enumerate(self.proxy) if x.protocol == protocol]

        if len(protocol_proxy_indexes) == 0:
            self.lack_of_proxy(protocol)
        elif len(protocol_proxy_indexes) == 1:
            self.used_proxy_index = 0
        else:
            previous_proxy_index = self.used_proxy_index
            while self.used_proxy_index == previous_proxy_index:
                self.used_proxy_index = random.choice(protocol_proxy_indexes)

        return {self.proxy[self.used_proxy_index].protocol: self.proxy[self.used_proxy_index].address}

    def draw_user_agent(self):
        if len(self.user_agents) == 0:
            self.lack_of_user_agent()
        elif len(self.user_agents) == 1:
            self.used_user_agent_index = 0
        else:
            previous_user_agent_index = self.used_user_agent_index
            while self.used_user_agent_index == previous_user_agent_index:
                self.used_user_agent_index = random.randint(0, len(self.user_agents)-1)

        return {'User-Agent': self.user_agents[self.used_user_agent_index]}

    def handle_connect_timeout(self, session, protocol):
        self.proxy[self.used_proxy_index].increment_timeout()
        self.proxy_connect_timeout(str(self.proxy[self.used_proxy_index]))

        if self.proxy[self.used_proxy_index].timeout_counter == self.max_proxy_timeouts:
            self.remove_proxy(self.used_proxy_index)
        session.proxies = self.draw_proxy(protocol)

    def handle_proxy_error(self, session, protocol):
        self.proxy_error(str(self.proxy[self.used_proxy_index]))
        self.remove_proxy(self.used_proxy_index)
        session.proxies = self.draw_proxy(protocol)

    def handle_invalid_header(self, session):
        self.invalid_user_agent(self.user_agents[self.used_user_agent_index])
        self.remove_user_agent(self.used_user_agent_index)
        session.headers = self.draw_user_agent()

    def handle_read_timeout(self):
        self.read_failure_counter += 1
        if self.read_failure_counter == self.max_read_failure:
            raise requests.ReadTimeout()

        self.read_failure(f'{self.read_failure_counter}/{self.max_read_failure}')

    def remove_proxy(self, index):
        del self.proxy[index]

        if index == self.used_proxy_index:
            self.used_proxy_index = -1

        if len(self.proxy) == 0:
            self.proxy_exhausted()

    def remove_user_agent(self, index):
        del self.user_agents[index]

        if index == self.used_user_agent_index:
            self.used_user_agent_index = -1

        if len(self.user_agents) == 0:
            self.user_agents_exhausted()

    def reset_read_failure_counter(self):
        self.read_failure_counter = 0

    @event.signal
    def stealth_mode_changed(self, state):
        pass

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
    def read_failure(self, counter):
        pass

    @event.signal
    def lack_of_proxy(self, protocol):
        pass

    @event.signal
    def proxy_exhausted(self):
        pass

    @event.signal
    def lack_of_user_agent(self):
        pass

    @event.signal
    def user_agents_exhausted(self):
        pass


class Proxy:

    def __init__(self, protocol='', address=''):
        self.protocol = protocol
        self.address = address
        self.timeout_counter = 0

    def increment_timeout(self):
        self.timeout_counter += 1

    def __eq__(self, other):
        return self.protocol == other.protocol and self.address == other.address

    def __repr__(self):
        return self.protocol + ': ' + self.address

    def __bool__(self):
        return len(self.protocol) > 0 and len(self.address) > 0

    def __str__(self):
        return f'Proxy: {self.protocol}://{self.address}, Timeout counter: {self.timeout_counter}'
