FROM python:3.12-slim
COPY tests/backend/requirements-dev.lock /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
WORKDIR /workspace
USER 65534:65534
ENV PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
# Build once with network, then resolve image ID. Runtime uses that immutable ID offline.
