# install dependencies
FROM docker.io/nicocool84/slidge-builder AS builder

COPY poetry.lock pyproject.toml /build/
RUN poetry export --without-hashes >requirements.txt
RUN python3 -m pip install --requirement requirements.txt

# main container
FROM docker.io/nicocool84/slidge-base AS toxlidge

USER root
RUN apt-get update && apt-get install libc++1 libssl3 libtoxcore2 -y && \
ln -s /usr/lib/x86_64-linux-gnu/libtoxcore.so.2 /usr/lib/x86_64-linux-gnu/libtoxcore.so && \
ln -s /usr/lib/x86_64-linux-gnu/libtoxcore.so.2 /usr/lib/x86_64-linux-gnu/libtoxav.so && \
ln -s /usr/lib/x86_64-linux-gnu/libtoxcore.so.2 /usr/lib/x86_64-linux-gnu/libtoxencryptsave.so

USER slidge
COPY --from=builder /venv /venv
COPY ./toxlidge /venv/lib/python/site-packages/legacy_module

# dev container
FROM docker.io/nicocool84/slidge-dev AS dev

USER root
RUN apt-get update && apt-get install libc++1 libssl3 libtoxcore2 -y && \
ln -s /usr/lib/x86_64-linux-gnu/libtoxcore.so.2 /usr/lib/x86_64-linux-gnu/libtoxcore.so && \
ln -s /usr/lib/x86_64-linux-gnu/libtoxcore.so.2 /usr/lib/x86_64-linux-gnu/libtoxav.so && \
ln -s /usr/lib/x86_64-linux-gnu/libtoxcore.so.2 /usr/lib/x86_64-linux-gnu/libtoxencryptsave.so

COPY --from=builder /venv /venv
