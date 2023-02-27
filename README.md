# docker-mon
A python script to monitor Docker containers for new image versions. If new versions are detected an update will be performed if configured.
Telegram notification included.

## Usage
Get the code:
``git clone https://github.com/tgueldner/docker-mon.git``

Run the script:
``python3 main.py -c nginx -u``

Could be called in a cronjob.

## Help
``python3 main.py -h``:
