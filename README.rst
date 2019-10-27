.. role:: raw-html-m2r(raw)
   :format: html


Yandex Images Download
======================

Python Script to download images from Yandex.Images.

Features
========


* Checking for captcha presence
* Many options 
* Multiproccessing is avaible (option ``--num-workers``\ )
* Can output JSON information about download processing through all images (option ``--json``\ )

Main requirements
=================


* Python 3.7+
* `Selenium Wire <https://github.com/wkeeling/selenium-wire>`_ 1.0.8+
* Firefox, Chrome, Safari and Edge are supported

Installation
============


#. 
   Install script requirements using ``pip``\ :\ :raw-html-m2r:`<br>`
   ``$ pip install -r requirements.txt``

#. 
   Get `Selenium driver executable <https://www.seleniumhq.org/about/platforms.jsp>`_ for your browser and platform. Firefox, Chrome, Safari and Edge are supported. 
   Use option ``--driver-path`` to specify the driver's path or add the executable in your PATH.

Example of use
==============

Simple example of using keywords and limit arguments to download images using `Chrome WebDriver <https://sites.google.com/a/chromium.org/chromedriver/>`_

``$ python yandeximagesdownload.py Chrome --keywords "vodka, bears, balalaika" --limit 10``

Example of using keywords from input file with specific image extension/format

``$ python yandeximagesdownload.py Chrome --keywords_from_file input_example.txt --itype=png``

All other information about input arguments can be obtained with the ``--help`` argument.

Acknowledgements
================

Special thanks to Andrey Lyashko for code reviews.
Special thanks to Boris Kovarski (https://github.com/kovarsky) and Andrey Lyashko for backing the project.
