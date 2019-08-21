import argparse
import itertools
import json
import logging
import os
import pathlib
import re
import requests
import sys
import time

from bs4 import BeautifulSoup
from dataclasses import dataclass
from dataclasses_json import dataclass_json
from math import floor
from multiprocessing import Pool
from seleniumwire import webdriver
from typing import List, Union, Optional
from urllib.parse import urlparse, urlencode
from urllib3.exceptions import SSLError, NewConnectionError


Driver = Union[webdriver.Chrome, webdriver.Edge, webdriver.Firefox, webdriver.Safari]

driver_name_to_class_and_default_path = {
    'Chrome' : (webdriver.Chrome, 'chromedriver'),
    'Edge' : (webdriver.Edge, 'MicrosoftWebDriver.exe'),
    'Firefox' : (webdriver.Firefox, 'geckodriver'),
    'Safari' : (webdriver.Safari, '/usr/bin/safaridriver'),
}  # type: Dict[str, Tuple[Driver, str]]


def parse_args():
    parser = argparse.ArgumentParser()
    input_group = parser.add_mutually_exclusive_group(required=True)
    
    
    parser.add_argument("browser", 
                    help=("browser with WebDriver"),
                    type=str,
                    choices=list(driver_name_to_class_and_default_path))
    
    parser.add_argument("-dp", "--driver-path", 
                        help=("path to browers's WebDriver"),
                        type=str, default=None)

    input_group.add_argument("-k", "--keywords", 
                        help=("delimited list input, separated by a comma"), 
                        type=str, default=None)
    
    input_group.add_argument("-kf", "--keywords-from-file", 
                        help=("extract list of keywords from a text file. "
                              "one line = one keyword."), 
                        type=str, default=None)
    
    parser.add_argument("-q", "--quiet-mode", 
                        default=False, 
                        help="do not logging.info() messages", 
                        action="store_true")
    
    input_group.add_argument("-x", "--single-image", 
                        help="downloading a single image from URL", 
                        type=str, default=None)
    
    parser.add_argument("-o", "--output-directory", 
                        help=("download images in a specific main directory"),
                        type=str, default="downloads")
    
    parser.add_argument("-l", "--limit", 
                        help="delimited list input. default: 100", 
                        type=int, default = 100)
    
    size_group = parser.add_mutually_exclusive_group()
    
    size_group.add_argument("--isize", help="image size", 
                        type=str, default=None,
                        choices=["large", "medium", "small"])
    
    size_group.add_argument("--exact-isize", 
                        help=("exact image resolution"),
                        nargs=2, type=int, default=None)
    
    parser.add_argument("--iorient", 
                        help="orient of image", 
                        type=str, default=None,
                        choices=["horizontal", "vertical", "square"])
    parser.add_argument("--itype", 
                        help="image type", 
                        type=str, default=None,
                        choices=["photo", "clipart", "lineart",
                                 "face", "demotivator"])
    parser.add_argument("--color", 
                        help="filter on color", 
                        type=str, default=None,
                        choices=["color", "gray", "red", "orange", 
                                 "cyan", "yellow", "green", "blue", 
                                 "violet", "white", "black"])
    
    parser.add_argument("--extension", 
                        help="image extension type", 
                        type=str, default=None,
                        choices=["jpg", "png", "gifan"])
    
    parser.add_argument("--commercial", 
                        help="add commerce check", 
                        type=str, default=None,
                        choices=["1"])
    
    parser.add_argument("--recent", 
                        help="add recency check", 
                        type=str, default=None,
                        choices=["7D"])
    
    parser.add_argument("--json",
                        help="save results information to json file",
                        type=str, default=False)
    
    parser.add_argument("--num-workers",
                        help="number of workers",
                        type=int, default=0)
    
    args = parser.parse_args()

    return args
    

#####
@dataclass_json
@dataclass
class ImgUrlResult:
    status: str
    message: str
    img_url : str
    img_path: str
    
@dataclass_json
@dataclass
class PageResult:
    status: str
    message: str
    page : int
    errors_count : int
    img_url_results: List[ImgUrlResult]

@dataclass_json
@dataclass
class KeywordResult:
    status: str
    message: str
    keyword: str
    errors_count : int
    page_results: List[PageResult]
    
@dataclass_json
@dataclass
class DownloaderResult:
    status: str
    message: str
    keyword_results: List[KeywordResult]
    
#####
    
def filepath_fix_existing(directory_path : pathlib.Path,
                          name : str, 
                          filepath : pathlib.Path) -> pathlib.Path:
    """Expands name portion of filepath with numeric "(x)" suffix.
    """
    new_filepath = filepath
    if filepath.exists():
        for i in itertools.count(start = 1):
            new_name = f'{name} ({i}){filepath.suffix}'
            new_filepath = directory_path / new_name
            if not new_filepath.exists():
                break
    
    return new_filepath
    
def download_single_image(img_url : str,
                          output_directory : pathlib.Path,
                          sub_directory : str = "",
                          multiproccess = False) -> ImgUrlResult:
    img_url_result = ImgUrlResult(status = None,
                                  message = None,
                                  img_url = img_url,
                                  img_path = None)

    img_extensions = (".jpg", ".jpeg", ".jfif", "jpe", ".gif", 
                    ".png", ".bmp", ".svg", ".webp", ".ico")
    content_type_to_ext = {
        "image/gif" : ".gif", 
        "image/jpeg" : ".jpg", 
        "image/png" : ".png", 
        "image/svg+xml" : ".svg", 
        "image/x-icon" : ".ico"
        }

    try:
        response = requests.get(img_url, timeout = 10)
        
        data = response.content
        content_type = response.headers["Content-Type"]
    
        if response.ok:
            
            img_name = pathlib.Path(urlparse(img_url).path).name
            img_name = img_name[:YandexImagesDownloader.MAXIMUM_FILENAME_LENGTH]
            
            directory_path = output_directory / sub_directory
            directory_path.mkdir(parents=True, exist_ok=True)
            
            if multiproccess:
                img_name = f"[{os.getpid()}] {img_name}"
            
            img_path = directory_path / img_name
            if not any(img_path.name.endswith(ext) for ext in img_extensions):
                img_path = img_path.with_suffix(content_type_to_ext[content_type])
            
            img_path = filepath_fix_existing(directory_path, img_name, img_path)
            with open(img_path, "wb") as f:
                f.write(data)

            img_url_result.status = "success"
            img_url_result.message = "Downloaded the image."
            img_url_result.img_path = str(img_path)
        else:
            img_url_result.status = "fail"
            img_url_result.message = (f"img_url response is not ok."
                                    f" response: {response}.")

    except (KeyboardInterrupt, SystemExit):
        raise

    except (requests.exceptions.SSLError, 
            requests.exceptions.ConnectionError) as e:
        img_url_result.status = "fail"
        img_url_result.message = f"{type(e)}"
    
    except Exception as exception:
        img_url_result.status = "fail"
        img_url_result.message = (f"Something is wrong here.",
                            f" Error: {type(exception), exception}")
    
    if img_url_result.status == "fail":
        logging.info(f"    fail: {img_url} error: {img_url_result.message}")
    else:
        logging.info(f"    {img_url_result.message} ==> {img_path}")
    
    return img_url_result

#####

class YandexImagesDownloader():
    """Class to download images from yandex.ru
    """

    MAIN_URL = "https://yandex.ru/images/search"
    MAXIMUM_PAGES_PER_SEARCH = 50
    MAXIMUM_IMAGES_PER_PAGE = 30
    MAXIMUM_FILENAME_LENGTH = 50

    def __init__(self, 
                 driver: Driver, 
                 output_directory = "download/", 
                 limit = 100, 
                 isize = None,
                 exact_isize = None,
                 iorient = None,
                 extension = None,
                 color = None,
                 itype = None, 
                 commercial = None, 
                 recent = None,
                 pool = None):
        self.driver = driver
        self.output_directory = pathlib.Path(output_directory)
        self.limit = limit
        self.isize = isize
        self.exact_isize = exact_isize
        self.iorient = iorient
        self.extension = extension
        self.color = color
        self.itype = itype
        self.commercial = commercial
        self.recent = recent
        
        self.url_params = self.init_url_params()
        self.requests_headers = {
            'User-Agent' : (
                    "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML,"
                    " like Gecko) Chrome/41.0.2228.0 Safari/537.36"
                )
        }
        self.cookies = {}
        self.pool = pool
        
        logging.info(f'Output directory is set to "{self.output_directory}/"')
        logging.info(f"Limit of images is set to {self.limit}")

        
    def get_response(self):
        pathes = [request.path for request in self.driver.requests]
        request = self.driver.requests[pathes.index(self.driver.current_url)]
        return request.response

    def init_url_params(self):
        params = {
            "nomisspell" : 1,
            "isize" : self.isize, 
            "iw" : None,
            "ih" : None,
            "iorient" : self.iorient,
            "type" : self.extension,
            "color" : self.color,
            "itype" : self.itype,
            "commercial" : self.commercial,
            "recent" : self.recent
            }
        
        if self.exact_isize:
            width, height = self.exact_isize
            params["isize"] = "eq"
            params["iw"] = width
            params["ih"] = height

        return params
    
    def get_url_params(self, page, text):
        params = {
            "p" : page,
            "text" : text
            }
        params.update(self.url_params)
        
        return params
    
    def download_images_by_page(self, keyword, page, imgs_count,
                                sub_directory) -> PageResult:
        
        page_result = PageResult(status = None,
                                 message = None,
                                 page = page,
                                 errors_count = None,
                                 img_url_results = [])
        

        self.check_captcha_and_get(YandexImagesDownloader.MAIN_URL, 
                                   params = self.get_url_params(page, keyword))
        
        response = self.get_response()
        
        if not (response.reason == "OK"):
            page_result.status = "fail"
            page_result.message = (f"Page response is not ok."
                                    f" page: {page},",
                                    f" status_code: {response.status_code}.")
            page_result.errors_count = YandexImagesDownloader.MAXIMUM_IMAGES_PER_PAGE
            return page_result
        
        soup_page = BeautifulSoup(self.driver.page_source, "lxml")

        # Getting all image urls from page.
        tag_sepr_item = soup_page.find_all("div", class_ = "serp-item")
        serp_items = [json.loads(item.attrs["data-bem"])["serp-item"] 
                        for item in tag_sepr_item]
        img_hrefs = [key["img_href"] for key in serp_items]

        errors_count = 0
        for img_url in img_hrefs:
            if imgs_count >= self.limit:
                break

            if self.pool:
                img_url_result = self.pool.apply_async(
                    download_single_image, args = (img_url, self.output_directory, 
                                                   sub_directory, True)
                    )
            else:
                img_url_result = download_single_image(img_url, self.output_directory, 
                                                   sub_directory)
            
            page_result.img_url_results.append(img_url_result)
            
            imgs_count += 1
            
        if self.pool:
            for i, img_url_result in enumerate(page_result.img_url_results):
                page_result.img_url_results[i] = img_url_result.get()
        errors_count += sum(1 if page_result.status == "fail" else 0
                            for page_result in page_result.img_url_results)
            
        page_result.status = "success"
        page_result.message = f"All successful images from page {page} downloaded."
        page_result.errors_count = errors_count
        
        return page_result


    def download_images_by_keyword(self, keyword, 
                                   sub_directory = "") -> KeywordResult:
        keyword_result = KeywordResult(status = None, 
                                       message = None,
                                       keyword = keyword,
                                       errors_count = None,
                                       page_results = [])

        self.check_captcha_and_get(YandexImagesDownloader.MAIN_URL, 
                                   params={'text': keyword, 
                                           "nomisspell" : 1})
        response = self.get_response()

        if not (response.reason == "OK"):
            keyword_result = "fail"
            keyword_result.message = ("Failed to fetch a search page."
                                       f" url: {YandexImagesDownloader.MAIN_URL},"
                                       f" params: {{'text': {keyword}}},"
                                       f" status_code: {response.status_code}")
            return keyword_result

        soup = BeautifulSoup(self.driver.page_source, "lxml")


        # Getting last_page.
        tag_serp_list = soup.find("div", class_ = "serp-list")
        if not tag_serp_list:
            keyword_result.status = "success"
            keyword_result.message = f"No images with keyword {keyword} found."
            keyword_result.errors_count = 0
            logging.info(f"    {keyword_result.message}")
            return keyword_result
        serp_list = json.loads(tag_serp_list.attrs["data-bem"])["serp-list"]
        last_page = serp_list["lastPage"]
        actual_last_page = 1 + floor(self.limit / YandexImagesDownloader.MAXIMUM_IMAGES_PER_PAGE)


        logging.info(f"  Found {last_page+1} pages of {keyword}.")
        
        
        # Getting all images.
        imgs_count = 0
        errors_count = 0

        for page in range(last_page + 1):
            if imgs_count >= self.limit:
                break
            
            if page > actual_last_page:
                actual_last_page += 1
                
            logging.info(f"  Scrapping page {page+1}/{actual_last_page}...")
                
            page_result = self.download_images_by_page(keyword, page, 
                                                       imgs_count, sub_directory)
            keyword_result.page_results.append(page_result)
            
            imgs_count += sum(1 for img_url_result in page_result.img_url_results 
                              if img_url_result.status == "success")
            errors_count += page_result.errors_count

            time.sleep(0.5)  # bot id protection
            
        keyword_result.status = "success"
        keyword_result.message = f"All images for {keyword} downloaded!"
        keyword_result.errors_count = errors_count
        
        return keyword_result 


    def download_images(self, keywords : List[str]) -> DownloaderResult:
        dowloader_result = DownloaderResult(status = None,
                                            message = None,
                                            keyword_results = [])
        
        dowloader_result.status = "fail"
        
        for keyword in keywords:
            logging.info(f"Downloading images for {keyword}...")

            keyword_result = self.download_images_by_keyword(keyword, 
                                                             sub_directory = keyword)
            dowloader_result.keyword_results.append(keyword_result)

            logging.info(keyword_result.message)
            
            
        dowloader_result.status = "success"
        dowloader_result.message = "Everything is downloaded!"
            
        return dowloader_result
    
    
    class StopCaptchaInput(Exception):
        pass

    def check_captcha_and_get(self, url, params = None):
        """Checking for captcha on url and get url after that.
        If there is captcha, you have to type it in input() or quit."""

        url_with_params = f"{url}?{urlencode(params)}"
        
        del self.driver.requests
        self.driver.get(url_with_params)

        while True:
            soup = BeautifulSoup(self.driver.page_source, "lxml")
        
            if not soup.select(".form__captcha"):
                break
                
            logging.warning(f"Please, type the captcha in the browser,"
                            " then press Enter or type [q] to exit")
            reply = input()
            if reply == "q":
                raise YandexImagesDownloader.StopCaptchaInput()

            del self.driver.requests
            self.driver.get(url_with_params)


def get_driver(name: str, path: Optional[str]) -> Driver:
    driver_class, default_path = driver_name_to_class_and_default_path[name]
    
    return driver_class(executable_path=path or default_path)


def scrap(args):
    keywords = []
    
    if args.keywords:
        keywords.extend([str(item).strip() for item in args.keywords.split(",") 
                           if len(item)])

    if args.keywords_from_file:
        with open(args.keywords_from_file, "r") as f:
            keywords.extend([line.strip() for line in f])
    
    driver = get_driver(args.browser, args.browser_path)
    
    try:
        if args.num_workers:
            pool = Pool(args.num_workers)
        
        downloader = YandexImagesDownloader(driver, 
                                            args.output_directory, 
                                            args.limit, args.isize, 
                                            args.exact_isize, 
                                            args.iorient, 
                                            args.extension, 
                                            args.color, 
                                            args.itype, 
                                            args.commercial, 
                                            args.recent,
                                            pool)

        start_time = time.time()
        total_errors = 0
        
        if keywords:
            downloader_result = downloader.download_images(keywords)
            total_errors += sum(keyword_result.errors_count
                                for keyword_result in downloader_result.keyword_results)
    finally:
        driver.quit()
        if args.num_workers:
            pool.close()
            pool.join()

    if args.single_image:
        img_url_result = download_single_image(args.single_image, 
                                               pathlib.Path(args.output_directory))
        total_errors += 1 if img_url_result.status == "fail" else 0
        
    total_time = time.time() - start_time

    logging.info("\nEverything downloaded!")
    logging.info(f"Total errors: {total_errors}")
    logging.info(f"Total files downloaded: {args.limit - total_errors}")
    logging.info(f"Total time taken: {total_time} seconds.")
    if keywords and args.json:
        downloader_result_json = downloader_result.to_dict()  # pylint: disable=no-member
        json_path = pathlib.Path(args.output_directory) / pathlib.Path(args.json)
        pretty_json = json.dumps(downloader_result_json, indent=4, ensure_ascii=False)
        with open(json_path, "w", encoding = "utf-8") as f:
            f.write(pretty_json)
        logging.info(f"Fesults information saved: {json_path}.")
    
def setup_logging(quiet_mode):
    logging.basicConfig(level=logging.WARNING if quiet_mode 
                        else logging.INFO, format="%(message)s")
    selenium_logger = logging.getLogger('seleniumwire')
    selenium_logger.setLevel(logging.WARNING)
    

def main():
    try:
        args = parse_args()
        setup_logging(args.quiet_mode)
        scrap(args)
        
    except KeyboardInterrupt as e:
        logging.error("KeyboardInterrupt")
        sys.exit(1)

    except Exception as e:
        logging.error(e, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
