FROM python:3.12-slim

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN apt-get -y update &&  \ 
    apt-get install --no-install-recommends -y chromium-driver && \
    rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir -r requirements.txt

COPY src/ .

CMD [ "python", "./navtotickets.py" ]
