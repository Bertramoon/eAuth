import ipaddress


def is_ip(ip: str) -> bool:
    if not ip:
        return False
    try:
        ipaddress.ip_address(ip)
        return True
    except:
        pass
    return False


if __name__ == '__main__':
    print(is_ip("127.0.0.1"))
