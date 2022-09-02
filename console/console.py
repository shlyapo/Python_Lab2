
from serializer.fabrica import Factory
import argparse
import logging

DEFAULT_FILE_NAME = "serialized_file"

SAME_EXTENSION_ERROR = "Inputted file and target extension are the same."

logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

uargs = argparse.ArgumentParser(description="Console serialize")
uargs.add_argument(
    'path',
    type=str,
    help='Provide path to file'
)
uargs.add_argument(
    'extension',
    type=str,
    default='json',
    help='Provide target extension to convert'
)
uargs.add_argument(
    "-n",
    "--name",
    type=str,
    default=DEFAULT_FILE_NAME,
    help="Optional parameter to provide output file name"
)


def get_ext(filename: str):
    return filename.split('.')[-1]


def try_get_parser(ext: str):
    parser = None
    try:
        parser = Factory.get_parser(ext)
    except ValueError:
        logging.error("Wrong target extension. Please, use YAML, TOML or JSON.")
    finally:
        return parser


def parse_file(path: str):
    file_ext = get_ext(path)
    try:
        fp = open(path, "r")
    except FileNotFoundError:
        logging.error(f"Error while opening {path}. There is no such file.")
        return
    fp.close()

    parser = try_get_parser(file_ext)
    if parser is None:
        return

    obj = None
    try:
        obj = parser.load(path)
    except ValueError:
        logging.error('Value error of the file')
    except KeyError:
        logging.error('Key error of the file')
    return obj


def serialize(obj, ext: str, file_name=DEFAULT_FILE_NAME):
    parser = try_get_parser(ext)
    if parser is None:
        return

    file = file_name + f".{ext}"
    parser.dump(obj, file)


def make_conversion(path: str, ext: str, file_name=DEFAULT_FILE_NAME):
    if get_ext(path).lower() == ext.lower():
        logging.error("Inputted file's format same as inputted target extension.")
        return
    obj = parse_file(path)
    if obj is None:
        return
    serialize(obj, ext, file_name)


np = uargs.parse_args()
logging.info(f"Starting of conversion.\n Converting {np.path} file to {np.extension} extension.")
make_conversion(np.path, np.extension, np.name)
logging.info("Ending of conversion.")
