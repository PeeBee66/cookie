FROM ubuntu:latest

# Install Python and other dependencies
RUN apt-get update && \
    apt-get install -y python3 python3-pip wget curl unzip libnss3 \
    xvfb libxi6 libgconf-2-4 jq libjq1 libonig5 libxkbcommon0 libxss1 libglib2.0-0 \
    libatspi2.0-0 libgtk-3-0 libpango-1.0-0 libgdk-pixbuf2.0-0 libxcomposite1 \
    libxcursor1 libxdamage1 libxtst6 libappindicator3-1 libasound2 libatk1.0-0 \
    libc6 libcairo2 libcups2 libxfixes3 libdbus-1-3 libexpat1 libgcc1 libnspr4 \
    libgbm1 libpangocairo-1.0-0 libstdc++6 libx11-6 libx11-xcb1 libxcb1 libxext6 \
    libxrandr2 libxrender1 gconf-service ca-certificates fonts-liberation \
    libappindicator1 lsb-release xdg-utils

# Download and install Chrome browser
RUN CHROME_URL="https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/117.0.5938.88/linux64/chrome-linux64.zip" && \
    wget -q -O /tmp/chrome-linux64.zip $CHROME_URL && \
    unzip /tmp/chrome-linux64.zip -d /usr/bin && \
    mkdir /usr/bin/google-chrome && \
    mv /usr/bin/chrome-linux64/ /usr/bin/google-chrome && \
    chmod +x /usr/bin/google-chrome

# Clean up the downloaded zip file
RUN rm /tmp/chrome-linux64.zip

# Create a symbolic link for Chrome
RUN ln -s /usr/bin/google-chrome /usr/local/bin/chrome

# Download and install Chrome WebDriver
RUN CHROME_DRIVER_URL="https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/117.0.5938.88/linux64/chromedriver-linux64.zip" && \
    CHROME_DRIVER_VERSION=$(curl -sS $CHROME_DRIVER_URL | grep -oP '(\d+\.\d+\.\d+\.\d+)' | head -n 1) && \
    wget -q -O /tmp/chromedriver_linux64.zip $CHROME_DRIVER_URL && \
    rm -rf /usr/bin/chromedriver && \
    unzip /tmp/chromedriver_linux64.zip -d /tmp/ && \
    mv /tmp/chromedriver-linux64 /usr/bin/chromedriver && \
    chmod +x /usr/bin/chromedriver

# Clean up
RUN apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Create a symbolic link for Chromedriver
RUN ln -s /usr/bin/chromedriver /usr/local/bin/chromedriver

WORKDIR /app
COPY . /app

# Install Python dependencies
RUN pip3 install -r requirements.txt

EXPOSE 7007
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:7007", "app:app"]

