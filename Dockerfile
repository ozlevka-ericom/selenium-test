FROM ubuntu:16.04

#libx11-6 gconf2 fontconfig xserver-common chromium-chromedriver chromium-browser chromium-chromedriver xvfb xserver-xephyr
RUN apt-get update \
    && apt-get install -y python python-pip  wget

WORKDIR /tmp

RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google.list \
    && apt-get update -y \
    && apt-get install -y  \
    google-chrome-beta \
    x11vnc \
    xvfb \
    xfonts-100dpi \
    xfonts-75dpi \
    xfonts-scalable \
    xfonts-cyrillic

COPY dependencies.txt ./
RUN pip install --upgrade pip && pip install -r ./dependencies.txt

WORKDIR /opt/driver
COPY chromedriver /opt/google/
RUN chmod +x /opt/google/chromedriver

WORKDIR /opt/application
COPY   main.py test-url-list.txt ./


CMD ["python", "main.py"]
