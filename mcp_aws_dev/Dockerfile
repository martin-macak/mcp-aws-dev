FROM python:3.13-slim

RUN pip install \
    pyyaml \
    jq \
    boto3 \
    tomli \
    requests-auth-aws-sigv4 \
    datamodel-code-generator \
    pydantic \
    httpx \
    anyio \
    uv \
    ruff \
    requests \
    ;

WORKDIR /workspace



ENTRYPOINT ["python", "script.py"]
