import argparse
import logging
from .downloader import DRIVER_NAME_TO_CLASS


def parse_args():
    parser = argparse.ArgumentParser()
    input_group = parser.add_mutually_exclusive_group(required=True)

    parser.add_argument("browser",
                        help=("browser with WebDriver"),
                        type=str,
                        choices=list(DRIVER_NAME_TO_CLASS))

    parser.add_argument("-dp",
                        "--driver-path",
                        help=("path to brower's WebDriver"),
                        type=str,
                        default=None)

    input_group.add_argument(
        "-k",
        "--keywords",
        help=("delimited list input, separated by a comma"),
        type=str,
        default=None)

    input_group.add_argument("-kf",
                             "--keywords-from-file",
                             help=("extract list of keywords from a text file. "
                                   "one line = one keyword."),
                             type=str,
                             default=None)

    parser.add_argument("-q",
                        "--quiet-mode",
                        default=False,
                        help="do not logging.info() messages",
                        action="store_true")

    input_group.add_argument("-x",
                             "--single-image",
                             help="downloading a single image from URL",
                             type=str,
                             default=None)

    parser.add_argument("-o",
                        "--output-directory",
                        help=("download images in a specific main directory"),
                        type=str,
                        default="downloads")

    parser.add_argument("-l",
                        "--limit",
                        help="delimited list input. default: 100",
                        type=int,
                        default=100)

    size_group = parser.add_mutually_exclusive_group()

    size_group.add_argument("--isize",
                            help="image size",
                            type=str,
                            default=None,
                            choices=["large", "medium", "small"])

    size_group.add_argument("--exact-isize",
                            help=("exact image resolution"),
                            nargs=2,
                            type=int,
                            default=None)

    parser.add_argument("--iorient",
                        help="orient of image",
                        type=str,
                        default=None,
                        choices=["horizontal", "vertical", "square"])
    parser.add_argument(
        "--itype",
        help="image type",
        type=str,
        default=None,
        choices=["photo", "clipart", "lineart", "face", "demotivator"])
    parser.add_argument("--color",
                        help="filter on color",
                        type=str,
                        default=None,
                        choices=[
                            "color", "gray", "red", "orange", "cyan", "yellow",
                            "green", "blue", "violet", "white", "black"
                        ])

    parser.add_argument("--extension",
                        help="image extension type",
                        type=str,
                        default=None,
                        choices=["jpg", "png", "gifan"])

    parser.add_argument("--commercial",
                        help="add commerce check",
                        type=str,
                        default=None,
                        choices=["1"])

    parser.add_argument("--recent",
                        help="add recency check",
                        type=str,
                        default=None,
                        choices=["7D"])

    parser.add_argument("--json",
                        help="save results information to json file",
                        type=str,
                        default=False)

    parser.add_argument("--num-workers",
                        help="number of workers",
                        type=int,
                        default=0)

    args = parser.parse_args()

    return args
