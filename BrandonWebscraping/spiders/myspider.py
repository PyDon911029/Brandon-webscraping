import os
import scrapy
from scrapy import Selector
from scrapy import signals
from scrapy.signalmanager import dispatcher
from urllib.parse import urlparse
import json
import tldextract

class Myspider(scrapy.Spider):
    name = "myspider"
    allowed_domains = ["example.com"]
    user_agent = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1'
    successed_counts = 0    
    
    def start_requests(self):
        project_dir = os.getcwd()
        file_name = 'local_businesses.json'
        file_path = ""
        invalid_domain_file = open("invalid_domain.txt", "a")

        # Search for the file within the project folder
        for root, dirs, files in os.walk(project_dir):
            if file_name in files:
                file_path = os.path.join(root, file_name)
                break

        if file_path:
            with open(file_path, 'r') as f:
                data = json.load(f)
                urls = [url["url"] for url in data]
                if urls:
                    print("dssssdsdsdsdsdsdsdsdsdsdsdsdsdsdsdsdsdsd")
                    print(len(urls))
                    print("dssssdsdsdsdsdsdsdsdsdsdsdsdsdsdsdsdsdsd")
                    self.start_urls = urls
                    # self.start_urls = ["http://utahvalleymag.com/"]
                    for url in self.start_urls:
                        domain = tldextract.extract(url).registered_domain
                        if domain:
                            print("Valid domain name:", url)
                            yield scrapy.Request(url=url, callback=self.parse, errback=self.handle_failure, meta={'download_timeout': 10})
                        else:
                            invalid_domain_file.write(url + "\n")
                            print("Invalid domain name", url)
                else:
                    print("No URLs found in the JSON file.")
        else:
            print("URL file not found in the project folder.")

    
    def parse(self, response):
        successed_file = open("success.txt", "a")
        failed_file = open("fail.txt", "a")
        if response.status == 200:
            html = response.text
            
            selector = Selector(text=html)
            img_tags = selector.xpath("//img[contains(translate(@src, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'logo')]/@src").getall()
            
            if len(img_tags) != 0:
                img_tag = img_tags[0]
                self.successed_counts = self.successed_counts + 1
                print("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")
                print(img_tag)
                print(self.successed_counts)
                successed_file.write(img_tag + "\n")
            else:
                print("No logo found.")
                failed_file.write(response.request.url + "\n")
                failed_file.close
        else:
            print("fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff")
            print(response)
            
    def handle_failure(self, failure):
        print("fffffffffffffffffaaaaaaaaaiill")
        # log the failure
        self.logger.error(repr(failure))

        # get the original request
        request = failure.request

        # create a new request with the HTTPS version of the URL
        protocol = urlparse(request.url).scheme
        if protocol == 'http':
            https_url = request.url.replace('http://', 'https://')
            new_request = request.replace(url=https_url)

            # yield the new request
            yield new_request
        else:
            failed_file = open("fail.txt", "a")
            failed_file.write(request.url + "\n")
            failed_file.close
    
    def spider_closed(self, signal, sender, spider):
        print("Scraping finished!")
        print(self.successed_counts)
    
    dispatcher.connect(spider_closed, signal=signals.spider_closed)