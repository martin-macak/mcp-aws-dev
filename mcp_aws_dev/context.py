from dataclasses import dataclass


@dataclass
class AWSContext:
    profile_name: str


@dataclass
class AppContext:
    aws_context: AWSContext
