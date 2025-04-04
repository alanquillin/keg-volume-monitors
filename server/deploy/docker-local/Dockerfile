FROM keg-volume-monitor:dev as python-build

USER 0

COPY requirements.txt .

RUN pip install -U pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

COPY scripts/seed-db.py /keg-volume-monitor/api

WORKDIR /keg-volume-monitor/api

ENTRYPOINT []

CMD poetry run ./migrate.sh upgrade head && \
    poetry run python3 seed-db.py
