FROM python:3

RUN pip install --upgrade pip

WORKDIR ./

COPY requirements.txt .

ADD context_extractor.py /

RUN pip install -r requirements.txt

CMD [ "python", "./context_extractor.py" ]
