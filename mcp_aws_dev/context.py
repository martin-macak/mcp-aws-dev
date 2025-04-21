"""Context classes for AWS profile and application configuration.

This module provides data classes for managing AWS profiles and application context.
"""

import functools
import os
import time
import boto3
from dataclasses import dataclass
from pydantic import BaseModel, Field


class SessionCredentials(BaseModel):
    """Represents session credentials for an AWS profile.

    :ivar account_id: The account ID for the AWS profile.
    :type account_id: str
    :ivar access_key: The access key for the AWS profile.
    :type access_key: str
    :ivar secret_key: The secret key for the AWS profile.
    :type secret_key: str
    :ivar session_token: The session token for the AWS profile.
    :type session_token: str
    """

    access_key: str = Field(
        description="The access key for the AWS profile."
    )
    secret_key: str = Field(
        description="The secret key for the AWS profile."
    )
    session_token: str = Field(
        description="The session token for the AWS profile."
    )
    account_id: str = Field(
        description="The account ID for the AWS profile."
    )


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

    def get_session_credentials(self) -> SessionCredentials:
        """Get session credentials for the AWS profile.

        :return: Session credentials for the AWS profile.
        :rtype: dict
        """
        
        credentials = boto3.Session(profile_name=self.profile_name).get_credentials()
        return SessionCredentials(
            access_key=credentials.access_key,
            secret_key=credentials.secret_key,
            session_token=credentials.token,
            account_id=credentials.account_id,
        )

class AppContext(BaseModel):
    """Represents the application context configuration.

    :ivar aws_context: The AWS context configuration containing profile settings.
    :type aws_context: AWSContext
    """

    aws_context: AWSContext = Field(
        description="The AWS context configuration containing profile settings."
    )

