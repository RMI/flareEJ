import sys
sys.path.append('..')


if __name__ == '__main__':
    from keys import MyKeys
    mykey = MyKeys("../config.ini")

    print(mykey.sharepoint)