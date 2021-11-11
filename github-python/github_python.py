import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.downloadermiddlewares.retry import RetryMiddleware
from scrapy.utils.response import response_status_message

import json
from lxml import etree
import time


class JsonWriterPipeline:
    def __init__(self):
        self.items = {}

    def __del__(self):
        with open('python.jl', 'w', encoding='UTF-8') as f:
            for i in self.items.values():
                f.write(json.dumps(i)+"\n")

    def process_item(self, item, spider):
        k = item["url"]
        if k in self.items:
            self.items[k].update(item)
        else:
            self.items[k] = item
        return item


class TooManyRequestsRetryMiddleware(RetryMiddleware):
    def __init__(self, crawler):
        super(TooManyRequestsRetryMiddleware, self).__init__(crawler.settings)
        self.crawler = crawler

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def process_response(self, request, response, spider):
        if request.meta.get('dont_retry', False):
            return response
        elif response.status == 429:
            self.crawler.engine.pause()
            time.sleep(60)
            self.crawler.engine.unpause()
            reason = response_status_message(response.status)
            return self._retry(request, reason, spider) or response
        elif response.status in self.retry_http_codes:
            reason = response_status_message(response.status)
            return self._retry(request, reason, spider) or response
        return response


class GithubSpider(scrapy.Spider):
    name = "github"

    custom_settings = {
        'ITEM_PIPELINES': {'__main__.JsonWriterPipeline': 1},
        'RETRY_HTTP_CODES': [429],
        'DOWNLOADER_MIDDLEWARES': {
            'scrapy.downloadermiddlewares.retry.RetryMiddleware': None,
            '__main__.TooManyRequestsRetryMiddleware': 543,
        }
    }

    def start_requests(self):
        urls = [
            'https://github.com/topics/python?page={}'.format(i+1) for i in range(34)
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse_topic)

    def parse_topic(self, res):
        html = etree.HTML(res.body)
        usernames = html.xpath(
            "/html/body/div[4]/main/div[2]/div[2]/div/div[1]/article/div[1]/div/div[1]/h3/a[1]/text()")
        for i in range(1, len(usernames)+1):
            name = html.xpath(
                "/html/body/div[4]/main/div[2]/div[2]/div/div[1]/article[{}]/div[1]/div/div[1]/h3/a[2]/text()".format(i))
            name = "".join(name).strip(' \n')
            url = html.xpath(
                "/html/body/div[4]/main/div[2]/div[2]/div/div[1]/article[{}]/div[1]/div/div[1]/h3/a[2]/@href".format(i))
            url = "".join(url).strip(' \n')
            url = "https://github.com" + url
            yield scrapy.Request(
                url=url, callback=self.parse_page, cb_kwargs={"url": url})
            yield {
                "name": name,
                "url": url,
            }

    def parse_page(self, res, url):
        html = etree.HTML(res.body)
        star = ""
        fork = ""
        t1 = html.xpath(
            "/html/body/div[4]/div/main/div[@id='repository-container-header']/div[1]/ul/li")
        if len(t1) == 3:
            star = html.xpath(
                "/html/body/div[4]/div/main/div[@id='repository-container-header']/div[1]/ul/li[2]/a[2]/@aria-label")
            star = "".join(star).strip(' \n')
            if len(star) == 0:
                star = "ERROR"
            fork = html.xpath(
                "/html/body/div[4]/div/main/div[@id='repository-container-header']/div[1]/ul/li[3]/a[2]/@aria-label")
            fork = "".join(fork).strip(' \n')
            if len(fork) == 0:
                fork = "ERROR"
        else:
            star = html.xpath(
                "/html/body/div[4]/div/main/div[@id='repository-container-header']/div[1]/ul/li[3]/a[2]/@aria-label")
            star = "".join(star).strip(' \n')
            if len(star) == 0:
                star = "ERROR"
            fork = html.xpath(
                "/html/body/div[4]/div/main/div[@id='repository-container-header']/div[1]/ul/li[4]/a[2]/@aria-label")
            fork = "".join(fork).strip(' \n')
            if len(fork) == 0:
                fork = "ERROR"

        titles = []
        title_size = len(html.xpath(
            "/html/body/div[4]/div/main/div[contains(@class, 'clearfix')]/div/div/div[2]/div[2]/div/div"))
        for i in range(title_size):
            t = html.xpath(
                "/html/body/div[4]/div/main/div[contains(@class, 'clearfix')]/div/div/div[2]/div[2]/div/div[{}]/div/h2/text()".format(i+1))
            t = "".join(t).strip(' \n')
            if len(t) == 0:
                t = html.xpath(
                    "/html/body/div[4]/div/main/div[contains(@class, 'clearfix')]/div/div/div[2]/div[2]/div/div[{}]/div/h2/a/text()".format(i+1))
                t = "".join(t).strip(' \n')
            titles.append(t)

        about = ""
        readme = ""
        topic = []
        try:
            about_idx = titles.index('About')
            about = html.xpath(
                "/html/body/div[4]/div/main/div[contains(@class, 'clearfix')]/div/div/div[2]/div[2]/div/div[{}]/div/p/text()".format(about_idx+1))
            about = "".join(about).strip(' \n')
            if len(about) == 0:
                about = "ERROR"
            topic = html.xpath(
                "/html/body/div[4]/div/main/div[contains(@class, 'clearfix')]/div/div/div[2]/div[2]/div/div[{}]/div/div/div/a/text()".format(about_idx+1))
            topic = [i.strip(' \n') for i in topic]
            n = html.xpath(
                "/html/body/div[4]/div/main/div[contains(@class, 'clearfix')]/div/div/div[2]/div[2]/div/div[{}]/div/div".format(about_idx+1))
            n = len(n)
            for i in range(n):
                t = html.xpath(
                    "/html/body/div[4]/div/main/div[contains(@class, 'clearfix')]/div/div/div[2]/div[2]/div/div[{}]/div/div[{}]/a/text()".format(about_idx+1, i+1))
                t = "".join(t).strip(' \n')
                if t == "Readme":
                    r = html.xpath(
                        "/html/body/div[4]/div/main/div[contains(@class, 'clearfix')]/div/div/div[2]/div[2]/div/div[{}]/div/div[{}]/a/@href".format(about_idx+1, i+1))
                    readme = "".join(r)
        except ValueError:
            pass

        release = "0"
        try:
            release_idx = titles.index('Releases')
            release = html.xpath(
                "/html/body/div[4]/div/main/div[contains(@class, 'clearfix')]/div/div/div[2]/div[2]/div/div[{}]/div/h2/a/span/text()".format(release_idx+1))
            release = "".join(release).strip(' \n')
            if len(release) == 0:
                release = "0"
        except ValueError:
            pass

        contributors = "1"
        try:
            con_idx = titles.index('Contributors')
            contributors = html.xpath(
                "/html/body/div[4]/div/main/div[contains(@class, 'clearfix')]/div/div/div[2]/div[2]/div/div[{}]/div/h2/a/span/text()".format(con_idx+1))
            contributors = "".join(release).strip(' \n')
        except ValueError:
            pass

        languages = {}
        try:
            lang_idx = titles.index('Languages')
            lang_name = html.xpath(
                "/html/body/div[4]/div/main/div[contains(@class, 'clearfix')]/div/div/div[2]/div[2]/div/div[{}]/div/ul/li/a/span[1]/text()".format(lang_idx+1))
            lang_perc = html.xpath(
                "/html/body/div[4]/div/main/div[contains(@class, 'clearfix')]/div/div/div[2]/div[2]/div/div[{}]/div/ul/li/a/span[2]/text()".format(lang_idx+1))
            languages = dict(zip(lang_name, lang_perc))
        except ValueError:
            pass

        branch = html.xpath(
            "/html/body/div[4]/div/main/div[contains(@class, 'clearfix')]/div/div/div[2]/div[1]/div[1]/div[2]/a[1]/strong/text()")
        branch = "".join(branch).strip(' \n')

        issue_url = res.url + "/issues"
        yield scrapy.Request(url=issue_url, callback=self.parse_issue, cb_kwargs={"url": url})
        pulls_url = res.url + "/pulls"
        yield scrapy.Request(url=pulls_url, callback=self.parse_pulls, cb_kwargs={"url": url})
        dependency_url = res.url + "/network/dependencies"
        yield scrapy.Request(
            url=dependency_url, callback=self.parse_dependency, cb_kwargs={"url": url})
        yield {
            "url": url,
            "star": star,
            "fork": fork,
            "about": about,
            "readme": readme,
            "topic": topic,
            "release": release,
            "contributors": contributors,
            "languages": languages,
            "branch": branch,
        }

    def parse_issue(self, res, url):
        html = etree.HTML(res.body)
        issues_open = html.xpath(
            '/html/body/div[4]/div/main/div/div/div/div/div/div/div/div/a[1]/text()')
        issues_open = "".join(issues_open).strip(' \n')
        if len(issues_open) == 0:
            issues_open = "0"
        issues_closed = html.xpath(
            '/html/body/div[4]/div/main/div/div/div/div/div/div/div/div/a[2]/text()')
        issues_closed = "".join(issues_closed).strip(' \n')
        if len(issues_closed) == 0:
            issues_closed = "0"
        yield {
            "url": url,
            "issues_open": issues_open,
            "issues_closed": issues_closed,
        }

    def parse_pulls(self, res, url):
        html = etree.HTML(res.body)
        pulls_open = html.xpath(
            '/html/body/div[4]/div/main/div/div/div/div/div/div/div/div/a[1]/text()')
        pulls_open = "".join(pulls_open).strip(' \n')
        if len(pulls_open) == 0:
            pulls_open = "0"
        pulls_closed = html.xpath(
            '/html/body/div[4]/div/main/div/div/div/div/div/div/div/div/a[2]/text()')
        pulls_closed = "".join(pulls_closed).strip(' \n')
        if len(pulls_closed) == 0:
            pulls_closed = "0"
        yield {
            "url": url,
            "pull_requests_open": pulls_open,
            "pull_requests_closed": pulls_closed,
        }

    def parse_dependency(self, res, url):
        html = etree.HTML(res.body)
        dependency = html.xpath(
            '/html/body/div[4]/div/main/div/div/div/div/div/div/div[contains(@class, "border-top")]/div/span/a/@href')
        yield {
            "url": url,
            "dependency": dependency,
        }


process = CrawlerProcess({
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'accept-encoding': 'gzip, deflate, br',
    'sec-ch-ua-platform': '"Linux"',
    'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36',
})
process.crawl(GithubSpider)
process.start()
