FROM ubuntu:24.04

COPY --from=ghcr.io/astral-sh/uv:0.11.6 /uv /uvx /bin/

USER root

RUN apt-get update \
    && apt-get install --yes --no-install-recommends \
        ca-certificates \
        git \
        openjdk-17-jdk-headless \
    && rm -rf /var/lib/apt/lists/*

USER ubuntu

# Let uv provide the project-required CPython 3.13 on both amd64 and arm64,
# and expose its standard Python shims for interactive container use.
RUN uv python install 3.13 --default

ENV PATH="/home/ubuntu/.local/bin:${PATH}"
