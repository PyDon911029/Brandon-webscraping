import os
from bs4 import BeautifulSoup
import requests
import scrapy
from scrapy import Selector
from scrapy import signals
from scrapy.signalmanager import dispatcher
from urllib.parse import urlparse, urljoin
import json
from pathlib import Path
import tldextract
import subprocess
import time

class Myspider(scrapy.Spider):
    name = "myspider"
    allowed_domains = ["example.com"]
    user_agent = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1'
    successed_counts = 0
    timestamp = str(time.time())
    
    project_dir = os.getcwd()

    def is_relative(self, url):
        return not(bool(urlparse(url).netloc))

    def save_image_from_url(self, url, _host, save_path):
        session = requests.Session()
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537',
            'Referer': _host,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
        }
        response = session.get(url, headers=headers)
        if response.status_code == 200:
            try:
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                    f.close()
            except Exception as e:
                print(f"Error downloading file: {e}")
        else:
            print("Failed to download IMAGE file. Status code:", response.status_code)
    
    def save_svg_from_url(self, url, _host, save_path):
        session = requests.Session()
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537',
            'Referer': _host,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
        }
        response = session.get(url, headers=headers)
        if response.status_code == 200:
            try:
                svg_content = response.content.decode('utf-8')
                soup = BeautifulSoup(svg_content, 'xml')
                with open(save_path, 'w') as f:
                    f.write(str(soup))
                    f.close()
                print("SVG file downloaded and processed successfully.")
            except UnicodeDecodeError:
                print("Failed to decode SVG content. Encoding error.")
        else:
            print("Failed to download SVG file. Status code:", response.status_code)
        
    def start_requests(self):
        file_name = 'local_businesses.json'
        path = os.path.normpath(self.project_dir)
        failed_path = Path(self.project_dir + '/failed_urls')
        if not failed_path.exists():
            failed_path.mkdir()
        if os.path.isdir(path):
            subprocess.run([os.path.join(os.getenv('WINDIR'), 'explorer.exe'), path])
        elif os.path.isfile(path):
            subprocess.run([os.path.join(os.getenv('WINDIR'), 'explorer.exe'), '/select,', os.path.normpath(path)])
        file_path = ""
        for root, dirs, files in os.walk(self.project_dir):
            if file_name in files:
                file_path = os.path.join(root, file_name)
                break
        if file_path:
            with open(file_path, 'r') as f:
                data = json.load(f)
                urls = [url["url"] for url in data]
                if urls:
                    self.start_urls = urls
                    for url in self.start_urls:
                        domain = tldextract.extract(url).registered_domain
                        if domain:
                            print("Valid domain name:", url)
                            yield scrapy.Request(url=url, callback=self.parse, errback=self.handle_failure, meta={'download_timeout': 30})
                        else:
                            invalid_domain_file = open(os.path.join(path, "invalid_domain" + self.timestamp + ".txt"), "a")
                            invalid_domain_file.write(url + "\n")
                            invalid_domain_file.close()
                            print("Invalid domain name", url)
                else:
                    print("No URLs found in the JSON file.")
                f.close()
        else:
            print("URL file not found in the project folder.")

    
    def parse(self, response):
        if response.status == 200:
            html = response.text
            selector = Selector(text=html)
            img_urls = selector.xpath("//img[contains(translate(@src, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'logo')]/@src").getall()
            
            if len(img_urls) != 0:
                img_url = img_urls[0]
                if self.is_relative(img_url):
                    img_url = urljoin(response.request.url, img_url)
                url_fn = os.path.basename(urlparse(img_url).path)
                path = Path(self.project_dir + '/output')
                if not path.exists():
                    path.mkdir()
                domain = tldextract.extract(response.request.url).registered_domain
                output_file_path = os.path.join(path, url_fn)
                if url_fn.split(".")[-1] == 'svg':
                    self.save_svg_from_url(img_url, response.request.url, output_file_path)
                else:
                    self.save_image_from_url(img_url, response.request.url, output_file_path)
                os.rename(output_file_path, 
                          os.path.join(path, domain + '.' + url_fn.split(".")[-1]))
            else:
                print("No logo found.")
                failed_file = open(os.path.join(path, "fail" + self.timestamp + ".txt"), "a")
                failed_file.write(response.request.url + "\n")
                failed_file.close()
        else:
            print(response)
            
    def handle_failure(self, failure):
        self.logger.error(repr(failure))
        request = failure.request
        protocol = urlparse(request.url).scheme
        if protocol == 'http':
            https_url = request.url.replace('http://', 'https://')
            new_request = request.replace(url=https_url)
            yield new_request
        else:
            failed_file = open("fail" + self.timestamp + ".txt", "a")
            failed_file.write(request.url + "\n")
            failed_file.close
    
    def spider_closed(self, signal, sender, spider):
        print("Scraping finished!")
        print(self.successed_counts)
    
    dispatcher.connect(spider_closed, signal=signals.spider_closed)