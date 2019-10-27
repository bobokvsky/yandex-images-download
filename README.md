# Yandex Images Download
Python Script to download images from Yandex.Images.

# Features
* Checking for captcha presence
* Many filters
* Multiproccessing is available (option `--num-workers`)

# Main requirements
* Python 3.7+
* [Selenium Wire](https://github.com/wkeeling/selenium-wire) 1.0.8+
* Firefox, Chrome, Safari and Edge are supported

# Installation
1. Get [Selenium driver executable](https://www.seleniumhq.org/about/platforms.jsp) for your browser and platform. Firefox, Chrome, Safari and Edge are supported.  
Use option `--driver-path` to specify the driver's path or add the executable in your PATH.


# Examples
Simple example using [Chrome WebDriver](https://sites.google.com/a/chromium.org/chromedriver/):

```$ yandex-images-download Chrome --keywords "vodka, bears, balalaika" --limit 10```

Example of using keywords from input file with specific image extension/format:

```$ yandex-images-download Chrome --keywords_from_file input_example.txt --itype=png```

All other information can be obtained with the `--help` argument.


# Acknowledgements
Special thanks to Andrey Lyashko for code reviews.  
Special thanks to Boris Kovarski (https://github.com/kovarsky) and Andrey Lyashko for backing the project.
