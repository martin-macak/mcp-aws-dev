[![Build](https://github.com/martin-macak/mcp-aws-dev/actions/workflows/build.yml/badge.svg?branch=main)](https://github.com/martin-macak/mcp-aws-dev/actions/workflows/build.yml)

# MCP for development on AWS

## Local testing

### Claude

Put this into your mcp config

```json
"aws_dev": {
    "command": "uv",
    "args": [
    "run",
    "--project",
    "/Users/martinmacak/projects/mcp-aws-dev",
    "mcp-aws-dev"
    ]
}
```

just replace the path to your local mcp-aws-dev repo
