# WebScrapper

WebScrapper is a program developed in Python 3.7 which allows you to scrap a website. You can use Scrapper class to scrap with your ip/user-agent or StealthScrapper which uses proxy and different user agents. The program also implements simple event system similar to the one that is implemented in Qt.


# Scrapping

Using Scrapper is fairly straightforward. You just have to use scrape method with a url that you want to scrap. You can set your own minimum/maximum delay, timeout time, maximum ticks for connect timeout, read timeout or connection error. When connec timeout/read timeout/connection errors will exceed maximum ticks that you assigned for them, then you will be informed about this with exception.

With StealthScrapper in default proxy is provided from the Internet, but you can change this by setting proxy_from_file parameter to True and provide proxy from files/proxy.txt. The format is like this:

protocol;ip;port</br>
https;190.13.14.34;8080

Proxy and user agent are changed every time when there is an error or when a scrapping was successfull. But when invoking scrape method you can invoke it like this: scrapper.scrape(url, False). Program will retain a proxy and a user agent from a previous scrapping process and won't change it if it isn't needed.


# Event

In order to use event system:
1. Your class have to derive from event.Subject,
2. Your class have to implement signal method like this one:
```
    @event.signal
    def connect_timeout(self, timeout_info):
        pass
```
3. You have to invoke signal in one of your's class methods:
```
    def invoke_connect_timeout(self):
        ...
        self.connect_timeout('TIMEOUT INFO')
```
4. You have to connect signal to a method or a function:
-For a given method from scrapper_example.py:
```
    def on_connect_timeout(self, timeout_info):
        self.logger.warning(f'Connect timeout: {timeout_info}')
```
You have to connect it like this:
```
    event.connect(scrapper, scrapper.connect_timeout, logger.on_connect_timeout)
```
-If it would be a function instead of a method:
```
    event.connect(scrapper, scrapper.connect_timeout, on_connect_timeout)
```
