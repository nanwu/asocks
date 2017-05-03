import configparser

config_parser = configparser.ConfigParser()
config_parser.read('example.ini')

config = {}
for name in config_parser['DEFAULT']:
    if name.endswith('port'):
        config[name] = config_parser['DEFAULT'].getint(name) 

globals().update(config)
