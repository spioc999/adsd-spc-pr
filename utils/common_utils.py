from netifaces import interfaces, ifaddresses, AF_INET


def get_host_address():
    for ifaceName in interfaces():
        addresses = ' '.join([i['addr'] for i in ifaddresses(ifaceName).setdefault(AF_INET, [{'addr': ''}])])
        if addresses != '' and addresses != '0.0.0.0' and addresses != '127.0.0.1':
            return addresses
    return '127.0.0.1'
