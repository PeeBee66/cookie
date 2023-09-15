FROM python:3.10.6
WORKDIR /app
COPY . /app
RUN apt-get install -y chromium-browser
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt
EXPOSE 5000
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]


sudo apt-get install chromium-browser
apt-get install libnss3
