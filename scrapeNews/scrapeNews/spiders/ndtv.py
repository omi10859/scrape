# -*- coding: utf-8 -*-
import scrapy
from scrapeNews.items import ScrapenewsItem
import time
import logging
import requests
from lxml import html
from datetime import datetime


class NdtvSpider(scrapy.Spider):


    name = 'ndtv'
    start_urls = ['http://www.ndtv.com/latest/']
    custom_settings = {
        'site_id':104,
        'site_name':'NDTV',
        'site_url':'https://www.ndtv.com/latest/page-1'}


    def __init__(self, pages=1, *args, **kwargs):
        super(NdtvSpider, self).__init__(*args, **kwargs)
        self.pages = pages

    def closed(self, reason):
        self.postgres.closeConnection(reason)


    def parse(self, response):
        page_ctr = 1
        while page_ctr <= int(self.pages):
            time.sleep(2)
            next_page = 'http://www.ndtv.com/latest/page-' + str(page_ctr)
            yield scrapy.Request(next_page, callback=self.parse_news)
            page_ctr += 1

    def parse_news(self, response):
        item = ScrapenewsItem()  # Scraper Items
        for news in response.css('div.new_storylising>ul>li'):
                if news.css('div.nstory_header>a::text'):
                    item['image'] = news.css('div.new_storylising_img>a>img::attr(src)').extract_first()
                    item['title'] = news.css('div.nstory_header>a::text').extract_first().strip()
                    item['content'] = news.css('div.nstory_intro::text').extract_first()
                    item['link'] = news.css('div.nstory_header>a::attr(href)').extract_first()
                    item['newsDate'] = self.parse_date(item['link'])
                    item['source'] = 104
                    yield item
                else:
                    logging.debug('Skipping a News Item, most probably an Advertisment')

    def parse_date(self, link):
        page = requests.get(link)
        r = html.fromstring(page.content)
        if r.xpath('//span[@itemprop="dateModified"]/@content'):
            return r.xpath('//span[@itemprop="dateModified"]/@content')[0][:-6]
        elif r.xpath('//meta[@name="publish-date"]/@content'):
            try :
                date = r.xpath('//meta[@name="publish-date"]/@content')[0][:-6]
                date = (datetime.strptime(date, '%a, %d %b %Y %H:%M:%S')).strftime("%Y-%m-%dT%H:%M:%S")
            except ValueError:
                date = r.xpath('//meta[@name="publish-date"]/@content')[0][:-6]
                date = (datetime.strptime(date, '%a,%d %b %Y %H:%M:%S')).strftime("%Y-%m-%dT%H:%M:%S")
            return date
        elif r.xpath('//meta[@itemprop="dateModified"]/@content'):
            return r.xpath('//meta[@itemprop="dateModified"]/@content')[0][:-6]
        else :
            logging.critical('ADD THIS: ' + link)
            return None
