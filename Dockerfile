FROM python:3.10-slim

WORKDIR /app

# Cài dependencies cần thiết
RUN apt-get update && apt-get install -y \
        wget \
        unzip \
        curl \
        gnupg \
    && wget -q -O /tmp/chromedriver.zip https://storage.googleapis.com/chrome-for-testing-public/130.0.6723.69/linux64/chromedriver-linux64.zip \
    && wget -q -O /tmp/chrome.zip https://storage.googleapis.com/chrome-for-testing-public/130.0.6723.69/linux64/chrome-linux64.zip \
    && unzip /tmp/chromedriver.zip -d /usr/local/bin/ \
    && unzip /tmp/chrome.zip -d /usr/local/bin/ \
    && mv /usr/local/bin/chrome-linux64 /usr/local/bin/chrome \
    && chmod +x /usr/local/bin/chromedriver-linux64/chromedriver \
    && ln -sf /usr/local/bin/chromedriver-linux64/chromedriver /usr/bin/chromedriver \
    && wget -q -O /usr/share/keyrings/google-linux-signing-key.gpg https://dl.google.com/linux/linux_signing_key.pub \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-linux-signing-key.gpg] http://dl.google.com/linux/chrome/deb/ stable main" \
        > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update && apt-get install -y google-chrome-stable \
    && apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/*

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "run.py"]