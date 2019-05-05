from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.utils.project import get_project_settings
from scrapy.crawler import CrawlerProcess

import json
from urllib.parse import urlparse
import argparse
import os
from hashlib import md5
import re
import ctypes


class IvCrawler(CrawlSpider):
    custom_settings = {
        # 'USER_AGENT': 'Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; Googlebot/2.1; +http://www.google.com/bot.html) Safari/537.36',
        "USER_AGENT": "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.93 Safari/537.36",
        'LOG_LEVEL': 'INFO',
        # 'REDIRECT_ENABLED': False
        # "DOWNLOAD_DELAY": 0.05
    }

    name = "iv-crawler"
    url_list = {}
    olds = 0
    nomatch = 0

    def __init__(self, restrict_xpaths=[], ignore="", domain="", whitelist=[], **kwargs):
        if not domain.startswith("http"):
            domain = "http://" + domain
        self.start_urls = [domain]
        self.restrict_xpaths = restrict_xpaths

        d = urlparse(domain).netloc
        if domain.startswith("www."):
            d = domain[4:]

        self.whitelist = whitelist
        self.allowed_domains = [d, d + ":443"]
        self.rules = [Rule(LinkExtractor(allow=(), allow_domains=self.allowed_domains, deny=(ignore), deny_domains=()), callback='parse_item', follow=True)]

        fn = "pages/{}/url_list.json".format(d)
        try:
            os.makedirs(os.path.dirname(fn))
        except Exception:
            pass
        self.file = open(fn, "a+", buffering=1)
        self.file.seek(0)
        try:
            self.url_list = json.loads(self.file.read())
        except Exception as ex:
            print(ex)
            pass
        self.file.seek(0)
        super().__init__(**kwargs)

    def parse_item(self, response):
        ctypes.windll.kernel32.SetConsoleTitleW(f"no xpath {self.nomatch} | old {self.olds} | parsed {len(self.url_list)} | parsing {response.url}")
        for i in self.restrict_xpaths:
            if len(response.xpath(i)) > 0:
                self.olds += 1
                print(f"{self.olds} - old {response.url}")
                return
        for i in self.whitelist:
            if len(response.xpath(i)) > 0:
                md = md5()
                md.update(response.url.encode("utf8"))
                u = str(md.hexdigest())
                if u in list(self.url_list.keys()):
                    continue
                fn = f"pages/{self.allowed_domains[0]}/{u}.html"

                file = open(fn, "w+", encoding="utf8")
                file.write(response.body.decode("utf8"))  # windows-1252
                file.close()
                print(f"{len(self.url_list)} - {response.url}")
                self.url_list[u] = response.url
                self.file.seek(0)
                self.file.truncate(0)
                self.file.seek(0)
                self.file.write(json.dumps(self.url_list))
                self.file.seek(0)
                return
        self.nomatch += 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Download all the pages from website')
    parser.add_argument('domain', metavar='domain', type=str, help='domain to crawl')
    parser.add_argument('--ignore', '-i', help='regex with links to ignore (file or string)', nargs='+')
    parser.add_argument('--whitelist', '-w', help='xpath of what pages should be crawled', nargs='+')
    parser.add_argument('--restrict_xpaths', '-r', help='xpath to ignore', nargs='+')

    args = parser.parse_args()

    settings = get_project_settings()
    settings['LOG_LEVEL'] = 'INFO'
    settings["USER_AGENT"] = "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.93 Safari/537.36"

    process = CrawlerProcess(settings)

    ignore = ""
    try:
        c = open(args.ignore[0], "r")
        ignore = c.read()
        ignore = ignore.split("\n")
        c.close()
    except Exception as ex:
        ignore = args.ignore
    print(f"ignore: {ignore}")
    if args.restrict_xpaths is None:
        args.restrict_xpaths = []
    if args.whitelist is None:
        args.whitelist = []
    whitelist = [re.sub(r"has-class\((\".*?\")\)", "contains(concat(' ', normalize-space(@class), ' '), \\1)", i) for i in args.whitelist]
    restrict_xpaths = [re.sub(r"has-class\((\".*?\")\)", "contains(concat(' ', normalize-space(@class), ' '), \\1)", i) for i in args.restrict_xpaths]

    print(whitelist)
    process.crawl(IvCrawler, restrict_xpaths=restrict_xpaths, ignore=ignore, domain=args.domain, whitelist=args.whitelist)
    process.start()
