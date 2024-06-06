import yaml, os, logging, platform
from logging.handlers import TimedRotatingFileHandler

import lib

BASE_DIR = os.path.dirname(os.path.realpath(__file__))
SQL_DIR = '%s/%s' % (BASE_DIR, "sql")
CHARTDEF_DIR = '%s/pyapi/chartdefs' % (BASE_DIR)

config_path = ""
conf = yaml.load(open("%s/default.yaml" % BASE_DIR), Loader=yaml.FullLoader)
conf["is_test"] = False

def get_tmpdir():
    system = platform.system()

    if system == 'Windows':
        tmpdir = "c:\\windows\\temp"
    elif system == 'Linux':
        tmpdir = "/tmp"
    else:
        # Handle other operating systems if needed
        tmpdir = None

    return tmpdir



def setup_logging(conf_log={}):
    global log_file

    l = logging.getLogger('')
    if len(l.handlers) > 0:
        return

    loglevel = conf_log.get("loglevel", "INFO")
    filename = conf_log["filename"]
    logdir = conf_log.get("logdir", get_tmpdir())
    backup_count = conf_log.get("backup_count", 14)

    if not os.path.exists(logdir): 
        os.makedirs(logdir)
    log_file = "%s/%s" % (logdir, filename)

    level = None
    if loglevel == "ERROR":
        level = logging.ERROR
    if loglevel == "INFO":
        level = logging.INFO
    if loglevel == "DEBUG":
        level = logging.DEBUG


    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=level, format=log_format)

    #file_handler = RotatingFileHandler(log_file, maxBytes=max_bytes, backupCount=backup_count)
    file_handler = TimedRotatingFileHandler(log_file, when='midnight', interval=1, backupCount=backup_count)
    file_handler.setFormatter(logging.Formatter(log_format))

    l.addHandler(file_handler)



def loadConf(confpath):
    global conf
    global config_path
    config_path = confpath
    conf2 = yaml.load(open(confpath), Loader=yaml.FullLoader)
    lib.mergeJson(conf, conf2)

    if "logging" in conf.keys():
        setup_logging(conf["logging"])
