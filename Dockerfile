FROM python:slim

# Copy only setup.py to utilize build cache
WORKDIR /home
COPY setup.py README.md ./
RUN pip3 install .

# Bring over the code and reinstall
COPY . .
RUN pip3 install --no-deps .

ENTRYPOINT ["kobodl"]
