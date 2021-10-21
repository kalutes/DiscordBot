FROM python:3
COPY requirements.txt /usr/src/app/requirements.txt
WORKDIR /usr/src/app
RUN pip install -r requirements.txt
COPY . /usr/src/app
CMD ["bot.py"]
ENTRYPOINT ["python3"]