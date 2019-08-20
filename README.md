# Yandex Images Download
Python Script to download images from Yandex.Images.

# Features
* Checking for captcha presence
* Many options 
* Multiproccessing is avaible (option `--num-workers`)
* Can output JSON information about download processing through all images (option `--json`)

# Main requirements
* Python 3.7+
* [Selenium Wire](https://github.com/wkeeling/selenium-wire) 1.0.8+
* Firefox, Chrome, Safari and Edge are supported

# Installation
1. Install script requirements using `pip`:  
`$ pip install -r requirements.txt`

2. Get [Selenium driver executable](https://www.seleniumhq.org/about/platforms.jsp) for your browser and platform. Firefox, Chrome, Safari and Edge are supported. 
Use option `--driver-path` to specify the driver's path or add the executable in your PATH.


## Example of use
Simple example of using keywords and limit arguments to download images using [Chrome WebDriver](https://sites.google.com/a/chromium.org/chromedriver/)

```$ python yandeximagesdownload.py Chrome --keywords "vodka, bears, balalaika" --limit 10```

Example of using keywords from input file with specific image extension/format

```$ python yandeximagesdownload.py Chrome --keywords_from_file input_example.txt --itype=png```

All other information about input arguments can be obtained with the `--help` argument.
