import configparser

config_parser = configparser.ConfigParser()
config_parser.read('config.ini')

config = {}
for name in config_parser['networking']:
    config[name.upper()] = config_parser['networking'].getint(name) 

globals().update(config)
