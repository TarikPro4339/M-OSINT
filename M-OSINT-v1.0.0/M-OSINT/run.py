"""Start the local dashboard only after the loopback socket has bound."""
import argparse
import sys
import threading
import webbrowser

def main():
    if sys.version_info<(3,10):
        raise SystemExit('Python 3.10+ gerekli: https://www.python.org/downloads/')
    from mosint.server import Server
    from mosint import VERSION, AUTHOR
    args=argparse.ArgumentParser(description='M-OSINT local dashboard')
    args.add_argument('--port',type=int,default=8765)
    args.add_argument('--no-browser',action='store_true')
    options=args.parse_args()
    if not 0<=options.port<=65535:
        args.error('port must be 0–65535')
    try:
        server=Server(options.port)
    except OSError:
        raise SystemExit('Port kullanilamiyor. Baska bir port deneyin: python run.py --port 8766') from None
    print('\n  M-OSINT v'+VERSION+' // '+AUTHOR+'\n  '+server.origin+'\n  Stop: Ctrl+C | No telemetry | Network opt-in\n',flush=True)
    if not options.no_browser:
        timer=threading.Timer(0.5,lambda:webbrowser.open(server.origin))
        timer.daemon=True; timer.start()
    try:
        server.serve_forever(poll_interval=0.3)
    except KeyboardInterrupt:
        print('\nM-OSINT stopped.')
    finally:
        server.server_close()
        server.keys.clear()

if __name__=='__main__':
    main()
