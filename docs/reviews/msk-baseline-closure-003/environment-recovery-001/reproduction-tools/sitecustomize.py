"""Task-only Python external-network boundary; not an OS sandbox claim."""
import ipaddress
import sys

def local(host):
    if host in (None,'','localhost',b'localhost'): return True
    try:
        if isinstance(host,bytes): host=host.decode()
        return ipaddress.ip_address(host).is_loopback
    except ValueError: return False

def audit(event,args):
    if event=='socket.getaddrinfo' and not local(args[0]):
        raise PermissionError('MSK qualification external DNS disabled')
    if event=='socket.connect' and isinstance(args[1],tuple) and not local(args[1][0]):
        raise PermissionError('MSK qualification external connection disabled')
sys.addaudithook(audit)
