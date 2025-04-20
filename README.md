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
    "mcp",
    "run",
    "/Users/martinmacak/projects/mcp-aws-dev/mcp_aws_dev/server.py"
    ]
}
```

just replace the path to your local mcp-aws-dev repo