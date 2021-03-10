FROM python:3

RUN pip install --upgrade pip

WORKDIR ./

COPY requirements.txt .

ADD context_extractor.py /

RUN pip install -r requirements.txt
RUN py -m spacy download en_core_web_sm

CMD [ "python", "./context_extractor.py" ]
