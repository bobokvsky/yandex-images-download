import os
import requests
import re
import pathlib
import sys
import time
from bs4 import BeautifulSoup
import json
import argparse
from math import ceil

args_list = ["keywords", "keywords_from_file", "output_directory", "limit", 
            "isize", "exact_isize", "iorient", "type", "color", "itype", "commercial", "recent",
            "silent_mode", "single_image"]

def user_input():
    parser = argparse.ArgumentParser()
    parser.add_argument("-k", "--keywords", help="delimited list input, separated by a comma", type=str, required=False)
    parser.add_argument("-kf", "--keywords_from_file", help="extract list of keywords from a text file, one line = one keyword.", type=str, required=False)
    parser.add_argument("-o", "--output_directory", help="download images in a specific main directory", default = "downloads", type=str, required=False)
    parser.add_argument("-l", "--limit", help="delimited list input", default = 100, type=int, required=False)
    parser.add_argument("-s", "--isize", help="image size", type=str, required=False,
                        choices=["large","medium","small"])
    parser.add_argument("-es", "--exact_isize", help="exact image resolution \"WIDTH HEIGHT\"", nargs=2, type=int, required=False)
    parser.add_argument("-or", "--iorient", help="orient of image", type=str, required=False,
                        choices=["horizontal", "vertical", "square"])
    parser.add_argument("-t", "--type", help="image type", type=str, required=False,
                        choices=["photo","clipart","lineart","face","demotivator"])
    parser.add_argument("-co", "--color", help="filter on color", type=str, required=False,
                        choices=["color", "gray", "red", "orange", "cyan", "yellow", "green", "blue", "violet", "white", "black"])
    parser.add_argument("-it", "--itype", help="image extension type", type=str, required=False,
                        choices=["jpg","png","gifan"])
    parser.add_argument("-com", "--commercial", help="commercial check", type=str, required=False,
                        choices=["1"])
    parser.add_argument("-rct", "--recent", help="add checking recently", type=str, required=False,
                        choices=["7D"])

    parser.add_argument("-x", "--single_image", help="downloading a single image from URL", type=str, required=False)
    

    parser.add_argument("-sil", "--silent_mode", default=False, help="Remains silent. Does not print notification messages on the terminal", action="store_true")

    return parser

class YandexImagesDowload():
    """Class to download images from yandex.ru

    ////////// How requests are made
    Each request in Yandex images is as follows.

    Usually, we make the request on the site:
    >>> "https://yandex.ru/images/search?text=Putin"
    After getting request, the browser gets html of page 1 request.
    When the user is scrolling down, the Yandex automatically makes requests
    to get next pages and loads them to your browser.

    To see it, just loads these urls and compare them with the main url:
    >>> https://yandex.ru/images/search?p=0&text=Putin
    >>> https://yandex.ru/images/search?p=1&text=Putin
    >>> https://yandex.ru/images/search?p=2&text=Putin

    The number of images per page seems to depend on using sockets.
    requests.get() seems to return 30 images per page. (tested on my PC and on Linux server)
    On my PC, in Google Chrome, each page have 109 images.

    Pages are indexed from 0 to 49. (from 0 to 26 on Google Chrome).
    So, the maximum count of images is 1500. (and, by surprise, 1485 on Google Chrome)

    We can find the actual last page by following:
    1) Find tag <div> with class="serp-list".
    2) This tag has attribute called "data-bem" with JSON data: {"serp-list" : serp-list}
    3) serp-list has these keys: ("pageNum", "lastPage", "reqid"). 
        "lastPage" is the target. 
    //////////

    ////////// How "image box" is stored in html page file.
    0) First, we need get page source.
    1) Each found image "box" is stored into tag <div> with class="serp-item".
    2) This tag has attribute called "data-bem" with JSON data: {"serp-item" : serp-item}
    3) serp_item has these keys:
    ("reqid", "freshness", "preview", "dups", "thumb", "snippet", 
    "detail_url", "img_href", "useProxy", "pos", "id", "rimId", "docid", 
    "greenUrlCounterPath", "counterPath")

    The most interested keys are "img_href" and "snippet"
    a) "img_href" is the source url of image. 
    Example: "img_href": ("https://www.bestnews.kz/media/k2/items/"
                        "cache/b777a09d352b16a52af288cda2537345_XL.jpg")
    
    b) "snippet" has useful information about the source url.

    Example: {"title": "Как отметит свой 64-й день рождения Владимир Путин - Bestnew",
    "hasTitle": True,
    "text": "Как отметит свой 64-й день рождения Владимир <b>Путин</b>.",
    "url": ("https://www.bestnews.kz/index.php/bn-v-mire/item/"
            "7533-kak-otmetit-svoj-64-j-den-rozhdeniya-vladimir-putin/amp"),
    "domain": "Bestnews.kz",
    "redirUrl": ("https://www.bestnews.kz/index.php/bn-v-mire/item/
                7533-kak-otmetit-svoj-64-j-den-rozhdeniya-vladimir-putin/amp")}
    
    """

    MAXIMUM_PAGES_PER_SEARCH = 50  # read "How requests are made" for details
    MAXIMUM_IMAGES_PER_PAGE = 30 # read "How requests are made" for details

    def __init__(self):
        pass


    def build_url_parameters(self, arguments):
        """Function to build url of request based on arguments.
        Returns (str) build_url (example : "&nomisspell=1&isize=large&iorient=vertical&color=orange")
        Check filters on images.yandex.ru and script info for details.
        """
        
        built_url = ""
        params = ["isize", "exact_isize", "iorient", "type", "color", "itype", "commercial", "recent"]
        
        for param in params:
            value = arguments[param]
            if value is not None:
                if param == "exact_isize":
                    width, height = arguments["exact_isize"]
                    built_url += f"&isize=eq&iw={width}&ih={height}"
                else:
                    built_url += f"&{param}={arguments[param]}"

        return built_url

    def filename_fix_existing(self, filepath):
        """Expands name portion of filepath with numeric " (x)" suffix to
        return filename that doesn"t exist already.
        """
        if not os.path.isfile(filepath):
            return filepath
        path = pathlib.Path(filepath)
        dirpath = path.parent
        name = path.stem
        extension = path.suffix
    
        names = [x for x in os.listdir(dirpath) if x.startswith(name)]
        names = [pathlib.Path(x).stem for x in names]
        suffixes = [x.replace(name, "") for x in names]
        
        # filter suffixes that match " (x)" pattern
        suffixes = [x[2:-1] for x in suffixes if re.match(r" \([0-9]+\)", x)]
        
        new_idx = 1

        # get new_idx for file
        if len(suffixes):
            indexes  = sorted([int(x) for x in suffixes])
            new_idx = 1
            for i, idx in enumerate(indexes, start=1):
                new_idx = i + 1
                if i != idx:
                    new_idx = i
                    break
    
        new_filepath = f"{dirpath}{os.sep}{name} ({new_idx}){extension}"

        return new_filepath


    def download_single_image(self, img_url, directory, arguments, session):
        """Function to download a single image into directory using requests.Session()
        Returns status (success/fail), message and img_path"""

        img_extensions = (".jpg", ".jpeg", ".jfif", "jpe", ".gif", 
                        ".png", ".bmp", ".svg", ".webp", ".ico")
        img_content_types = {"image/gif" : ".gif", 
                            "image/jpeg" : ".jpg", 
                            "image/png" : ".png", 
                            "image/svg+xml" : ".svg", 
                            "image/x-icon" : ".ico"}
        img_path = ""

        try:
            response = session.get(img_url)
            
            data = response.content
            content_type = response.headers["Content-Type"]
        
            if response.ok:
                img_name = os.path.basename(img_url) # last part of url
                if img_name.find("?") != -1:
                    img_name = img_name[0:img_name.find("?")]  # remove "abc.jpg?options"
                if img_name.find("!") != -1:
                    img_name = img_name[0:img_name.find("!")]  # remove "abc.jpg!options"
                if not any(ext in img_name for ext in img_extensions):
                    img_name = img_name + img_content_types[content_type]
                
                img_path = os.path.normpath(directory + os.sep + img_name)
                img_path = self.filename_fix_existing(img_path)
                
                # create dir if not exists:
                pathlib.Path(directory).mkdir(parents=True, exist_ok=True) 
                with open(img_path, "wb") as f:
                    f.write(data)

                download_status = "success"
                download_message = "Downloaded Image"
            else:
                download_status = "fail"
                download_message = f"Response is not ok: {response}"


        except (KeyboardInterrupt, SystemExit):
            raise

        except requests.exceptions.SSLError:
            download_status = "fail"
            download_message = f"SSLError. Skipping."

        except requests.exceptions.ConnectionError:
            download_status = "fail"
            download_message = f"ConnectionError. Skipping."
        
        except Exception as exception:
            download_status = "fail"
            download_message = f"Something is wrong here. Error: {type(exception), exception}"
        
        if not arguments["silent_mode"]: 
            if download_status == "fail":
                print(f"    fail: {img_url} error: {download_message}")
            elif download_status == "success":
                print(f"    {download_message} ==> {img_path}")
        
        return download_status, download_message, img_path
    


    def download_images_by_keyword(self, keyword, arguments, session):
        """Function to download a many images from yandex images by specified keyword.
        Using requests.Session().
        Returns dict of statutes, messages and img_paths of each downloaded images.
        
        Example of output:
        {'testA': {'status': 'success', 'last_page': 1, 'errors_count': 0, 'page0': 
        {'img0': {'status': 'success', 'message': 'Downloaded Image', 'path': 'testA\\s1200.jpg'}, 
        'img1': {'status': 'success', 'message': 'Downloaded Image', 'path': 'testA\\testo_dlya_piccy_na_kefire.jpg.crop_display.jpg'}, 
        'img2': {'status': 'success', 'message': 'Downloaded Image', 'path': 'testA\\55c10a578ce3e.jpg'}}}}
        """

        keyword_dict_results = {}
        keyword_url = keyword.replace(" ", "%20")
        
        main_url = f"https://yandex.ru/images/search?text={keyword_url}"
        
        response = session.get(main_url)
        soup = BeautifulSoup(response.content, "lxml")


        keyword_dict_results["status"] = "success"
        keyword_dict_results["last_page"] = 0
        keyword_dict_results["errors_count"] = 0


        if not response.ok:
            keyword_dict_results["status"] = "fail"
            keyword_dict_results["message"] = (f"Something is wrong here."
                                            f"url: {main_url}, status_ok: {response.ok}")

            return keyword_dict_results

        soup = BeautifulSoup(response.content, "lxml")
        
        # Getting lastPage.
        # 1) Find tag <div> with class="serp-list".
        tag_sepr_list = soup.find("div", class_ = "serp-list")
        if tag_sepr_list:
            # 2) This tag has tag called "data-bem" with JSON data: {"serp-list" : serp-list}
            serp_list = json.loads(tag_sepr_list.attrs["data-bem"])["serp-list"]
            # 3) serp-list has these keys: ("pageNum", "lastPage", "reqid"). 
            last_page = serp_list["lastPage"]
        else:
            keyword_dict_results["status"] = "success"
            keyword_dict_results["message"] = (f"No images with keyword \"{keyword_url}\""
                                            " found. Skipping.")
            print(f"    {keyword_dict_results['message']}")
            
            return keyword_dict_results


        if not arguments["silent_mode"]: 
            print(f"  Found {last_page+1} pages of {keyword}.")

        actual_last_page = ceil(arguments["limit"] / YandexImagesDowload.MAXIMUM_IMAGES_PER_PAGE)
        keyword_dict_results["last_page"] = actual_last_page


        # Getting all images.
        output_directory = arguments["output_directory"]
        keyword_directory = output_directory + os.sep + keyword
        pathlib.Path(keyword_directory).mkdir(parents=True, exist_ok=True) 

        build_url = "&nomisspell=1"  # do not make misspell change
        built_url = build_url + self.build_url_parameters(arguments)

        limit = arguments["limit"]
        count_imgs = 0
            
        for page in range(last_page+1):

            if not arguments["silent_mode"]: 
                print(f"  Looking page {page+1}/{actual_last_page}...")

            keyword_dict_results[f"page{page}"] = {}
            url_page = f"https://yandex.ru/images/search?p={page}&text={keyword_url}" + built_url
            response_page = session.get(url_page)
            if not response_page.ok:
                keyword_dict_results[f"page{page}"]["status"] = "fail"
                keyword_dict_results[f"page{page}"]["message"] = (f"Something is wrong here."
                                        f"Page: {page}, status_ok: {response_page.ok}.")
            
            soup_page = BeautifulSoup(response_page.content, "lxml")

            # 1) Each found image is stored into <div> with class="serp-item".
            tag_sepr_item = soup_page.find_all("div", class_ = "serp-item")
            # 2) This tag has attribute called "data-bem" with JSON data: {"serp-item" : serp-item}
            serp_items = [json.loads(item.attrs["data-bem"])["serp-item"] for item in tag_sepr_item]
            # 3) In this JSON, img source is stored in "img_href"
            img_hrefs = [key["img_href"] for key in serp_items]


            for i, img_url in enumerate(img_hrefs):
                keyword_dict_results[f"page{page}"][f"img{i}"] = {}
                (download_status,
                download_message,
                img_path) = self.download_single_image(img_url, directory=keyword_directory,
                                                                arguments = arguments,
                                                                session = session)

                keyword_dict_results[f"page{page}"][f"img{i}"]["status"] = download_status
                keyword_dict_results[f"page{page}"][f"img{i}"]["message"] = download_message
                keyword_dict_results[f"page{page}"][f"img{i}"]["path"] = img_path

                if download_status == "success":
                    count_imgs += 1
                else:
                    keyword_dict_results["errors_count"] += 1

                if count_imgs > limit:
                    # exit from 2 loops
                    return keyword_dict_results

            time.sleep(0.3)  # bot id protection

        return keyword_dict_results 


    def download_images(self, keywords, arguments, session):
        """Function to download a many images from yandex images by list of keywords.
        Returns dict of dicts having [statutes, messages, img_paths] for each keywords."""

        results = {}
        print(f"Limit of images is set to {arguments['limit']}")
        for keyword in keywords:
            print(f"Downloading images for \"{keyword}\"...")

            self.check_captcha(session)
            results[keyword] = self.download_images_by_keyword(keyword, arguments, session)

            print(f"\"{keyword}\" finished!")

        return results

    def check_captcha(self, session):
        """Checking for captcha on url using requests.Session().
        If there is captcha, you have to fill it in input() or exit."""

        test_url = "https://yandex.ru/images/search?text=Test"
        c_url = "http://yandex.ru/checkcaptcha"
        response = session.get(test_url)

        while True:
            soup = BeautifulSoup(response.content, "lxml")
            if soup.select(".form__captcha"):
                
                captcha_url = soup.select('.form__captcha')[0].attrs['src']
                print(f"Captcha: {captcha_url}")
                reply = input("Please, write the captcha or [quit/exit/q] to exit: ")
                key = soup.select(".form__key")[0].attrs['value']
                retpath = soup.select('.form__retpath')[0].attrs['value']

                if reply == "quit" or reply == "q" or reply == "exit":
                    response.close()
                    sys.exit()
                else:
                    response = session.get(c_url, params={'key': key, 
                                                        'retpath': retpath, 
                                                        'rep': reply})
                                                    
            else:
                break




def keywords_from_file(file_name):
    """Returns list of keywords from file."""
    search_keyword = []
    with open(file_name, "r", encoding="utf-8") as f:
        for line in f:
            search_keyword.append(line.strip())
    
    return search_keyword

#------------- Main Program -------------#
def main():
    parser = user_input()

    args = parser.parse_args()
    arguments = vars(args)

    for arg in args_list:
        if arg not in arguments:
            arguments[arg] = None
    
    # Initialization and Validation of user arguments
    if arguments["keywords"]:
        search_keywords = [str(item) for item in arguments["keywords"].split(",") if len(item)]

    if arguments["keywords_from_file"]:
        search_keywords = keywords_from_file(arguments["keywords_from_file"])

    # both time and time range should not be allowed in the same query
    if arguments["isize"] and arguments["exact_isize"]:
        raise ValueError("Either \"size\" or \"exact_size\" should be used in a query."
                            "Both cannot be used at the same time.")

    # If single_image or url argument not present then keywords is mandatory argument
    if arguments['single_image'] is None and arguments['keywords'] is None \
            and arguments['keywords_from_file'] is None:
        
        parser.print_help()
        sys.exit(1)

    ###

    total_errors = 0

    downloader = YandexImagesDowload()
    session = requests.Session()
    downloader.check_captcha(session)

    time_start = time.time()

    if arguments["single_image"]:  # Download Single Image using a URL
        downloader.download_single_image(arguments["single_image"], arguments["output_directory"], 
                                        arguments, session)
    else:  # or download multiple images based on keywords search
        results = downloader.download_images(search_keywords, arguments, session)
        total_errors += sum(results[keyword]["errors_count"] for keyword in results if results[keyword]["status"] == "success")

    session.close()

    time_end = time.time() 
    total_time = time_end - time_start
    
    if not arguments["silent_mode"]:
        print("\nEverything downloaded!")
        print("Total errors: " + str(total_errors))
        print("Total time taken: " + str(total_time) + " Seconds")

if __name__ == "__main__":
    main()