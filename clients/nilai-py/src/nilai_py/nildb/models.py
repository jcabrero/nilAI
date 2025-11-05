"""
Common Pydantic models for nildb_wrapper package.

This module provides base models and common types used across all modules.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field
from secretvaults import SecretVaultUserClient
from secretvaults.common.keypair import Keypair


class BaseResult(BaseModel):
    """Base result model for all operations"""

    model_config = ConfigDict(
        extra="allow",
        validate_assignment=True,
        use_enum_values=True,
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )

    success: bool
    error: str | Exception | None = None
    message: str | None = None


class PromptDelegationToken(BaseModel):
    """Delegation token model"""

    model_config = ConfigDict(validate_assignment=True)

    token: str
    did: str


class TimestampedModel(BaseModel):
    """Base model with timestamp fields"""

    model_config = ConfigDict(extra="allow", validate_assignment=True, populate_by_name=True)

    created_at: datetime | None = Field(default_factory=datetime.now)
    updated_at: datetime | None = None


class KeyData(TimestampedModel):
    """Model for key data in JSON files"""

    type: str
    key: str
    name: str | None = None

    # For public keys
    did: str | None = None
    private_key_file: str | None = None

    # For private keys
    public_key_file: str | None = None


class KeypairInfo(BaseModel):
    """Information about stored keypairs"""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    private_key_file: str
    public_key_file: str | None = None
    created_at: str | None = None
    name: str = "unnamed"
    did: str = "unknown"


# User module models
class UserSetupResult(BaseResult):
    """Result of user setup operation"""

    user_client: SecretVaultUserClient | None = None
    keypair: Keypair | None = None
    keys_saved_to: dict[str, str] | None = None


# Collection module models
class CollectionResult(BaseResult):
    """Result of collection operations"""

    data: Any | None = None


class CollectionCreationResult(BaseResult):
    """Result of collection creation"""

    collection_id: str | None = None
    collection_name: str | None = None
    collection_type: str | None = None


# Document module models
class OperationResult(BaseResult):
    """Result of document operations"""

    data: Any | None = None


class DocumentReference(BaseModel):
    """Reference to a document"""

    model_config = ConfigDict(validate_assignment=True)

    builder: str
    collection: str
    document: str


# Builder module models
class RegistrationStatus(str, Enum):
    """Builder registration status"""

    SUCCESS = "success"
    ALREADY_REGISTERED = "already_registered"
    ERROR = "error"


class DelegationToken(BaseModel):
    """Delegation token model"""

    model_config = ConfigDict(validate_assignment=True)

    token: str
    did: str


class RegistrationResult(BaseResult):
    """Result of builder registration"""

    status: RegistrationStatus
    response: Any | None = None


class TokenData(TimestampedModel):
    """Delegation token data for JSON serialization"""

    type: str = "delegation_token"
    expires_at: datetime
    user_did: str
    builder_did: str
    token: str
    usage: str = "Use this token for data creation operations"
    valid_for_seconds: int = 60
