import configparser
config = configparser.ConfigParser()
config.read('config.ini')


class MyKeys:

    def __init__(self, config_file):
        config = configparser.ConfigParser()
        config.read(config_file)
        self.environment = config['VERSION']['ENVIRONMENT']
        self.sharepoint = config[f"{self.environment}"]['SHAREPOINT']


if __name__=="__main__":
    mykey = MyKeys("config.ini")
    print(mykey.environment)