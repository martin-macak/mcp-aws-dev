"""Context classes for AWS profile and application configuration.

This module provides data classes for managing AWS profiles and application context.
"""

import functools
import os
import time
import boto3
from dataclasses import dataclass
from pydantic import BaseModel, Field


class AWSProfile(BaseModel):
    """Represents an AWS profile configuration.

    :ivar profile_name: The name of the AWS profile used for AWS credentials.
    :type profile_name: str
    """

    profile_name: str = Field(
        description="The name of the AWS profile used for AWS credentials."
    )


class AWSContext(BaseModel):
    """Represents the AWS context configuration.

    :ivar profile_name: The name of the AWS profile to use for AWS operations.
    :type profile_name: str
    """

    profile_name: str = Field(
        description="The name of the AWS profile to use for AWS operations."
    )

    def get_session(self) -> boto3.Session:
        """Creates a new boto3 session for the current AWS profile.

        :return: A boto3 session configured with the current profile_name.
        :rtype: boto3.Session
        """
        return boto3.Session(profile_name=self.profile_name)


class AppContext(BaseModel):
    """Represents the application context configuration.

    :ivar aws_context: The AWS context configuration containing profile settings.
    :type aws_context: AWSContext
    """

    aws_context: AWSContext = Field(
        description="The AWS context configuration containing profile settings."
    )


def create_session(
    profile_name: str,
) -> boto3.Session:
    """Creates a new boto3 session for the given profile name.

    :param profile_name: The name of the AWS profile to use.
    :type profile_name: str
    :return: A boto3 session configured with the given profile name.
    :rtype: boto3.Session
    """

    cache_hash = int(time.time() / 3600)
    return _create_session_cached(profile_name, cache_hash)


@functools.cache
def _create_session_cached(
    profile_name: str,
    _cache_hash: int,
) -> boto3.Session:
    """Creates a new boto3 session for the given profile name.

    :param profile_name: The name of the AWS profile to use.
    :type profile_name: str
    :param _cache_hash: Cache invalidation hash.
    :type _cache_hash: int
    :return: A boto3 session configured with the given profile name.
    :rtype: boto3.Session
    """

    del _cache_hash
    return boto3.Session(profile_name=profile_name)
