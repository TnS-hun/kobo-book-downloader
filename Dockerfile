FROM python:alpine

# Copy only setup.py to utilize build cache
WORKDIR /home
COPY setup.py README.md ./
RUN apk add --no-cache gcc tini libc-dev \
  && pip3 install . \
  && apk del gcc libc-dev

# Bring over the code and reinstall
COPY . .
RUN pip3 install --no-deps .

ENTRYPOINT ["/sbin/tini", "--", "kobodl"]
