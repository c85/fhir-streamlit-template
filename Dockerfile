FROM python:3.10
COPY . /usr/app/
WORKDIR /usr/app/
RUN pip install -r requirements.txt
COPY index.html /usr/local/lib/python3.10/site-packages/streamlit/static/index.html
CMD streamlit run index.py --server.port 80