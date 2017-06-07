import configparser 

config_parser = configparser.ConfigParser()
config_parser.read('proxy.ini')

proxy_config = {}
for name in config_parser['networking']:
    if name == 'proxy_local_port':
        proxy_config[name.upper()] = config_parser['networking'].getint(name)

globals().update(proxy_config)
