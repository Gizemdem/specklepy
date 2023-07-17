import os
from typing import List, Optional

from pydantic import BaseModel, Field  # pylint: disable=no-name-in-module

from specklepy.api.models import ServerInfo
from specklepy.core.helpers import speckle_path_provider
from specklepy.logging import metrics
from specklepy.logging.exceptions import SpeckleException
from specklepy.transports.sqlite import SQLiteTransport

# following imports seem to be unnecessary, but they need to stay 
# to not break the scripts using these functions as non-core
from specklepy.core.api.credentials import (UserInfo, 
                                            StreamWrapper, # deprecated 
                                            get_local_accounts as core_get_local_accounts, 
                                            get_account_from_token as core_get_account_from_token)


class Account(BaseModel):
    isDefault: bool = False
    token: Optional[str] = None
    refreshToken: Optional[str] = None
    serverInfo: ServerInfo = Field(default_factory=ServerInfo)
    userInfo: UserInfo = Field(default_factory=UserInfo)
    id: Optional[str] = None

    def __repr__(self) -> str:
        return (
            f"Account(email: {self.userInfo.email}, server: {self.serverInfo.url},"
            f" isDefault: {self.isDefault})"
        )

    def __str__(self) -> str:
        return self.__repr__()

    @classmethod
    def from_token(cls, token: str, server_url: str = None):
        acct = cls(token=token)
        acct.serverInfo.url = server_url
        return acct


def get_local_accounts(base_path: Optional[str] = None) -> List[Account]:
    """Gets all the accounts present in this environment

    Arguments:
        base_path {str} -- custom base path if you are not using the system default

    Returns:
        List[Account] -- list of all local accounts or an empty list if
        no accounts were found
    """
    accounts = core_get_local_accounts(base_path)

    metrics.track(
        metrics.SDK,
        next(
            (acc for acc in accounts if acc.isDefault),
            accounts[0] if accounts else None,
        ),
        {"name": "Get Local Accounts"}
    )

    return accounts

def get_default_account(base_path: Optional[str] = None) -> Optional[Account]:
    """
    Gets this environment's default account if any. If there is no default,
    the first found will be returned and set as default.
    Arguments:
        base_path {str} -- custom base path if you are not using the system default

    Returns:
        Account -- the default account or None if no local accounts were found
    """
    accounts = core_get_local_accounts(base_path=base_path)
    if not accounts:
        return None

    default = next((acc for acc in accounts if acc.isDefault), None)
    if not default:
        default = accounts[0]
        default.isDefault = True
    metrics.initialise_tracker(default)

    return default
    
def get_account_from_token(token: str, server_url: str = None) -> Account:
    """Gets the local account for the token if it exists
    Arguments:
        token {str} -- the api token

    Returns:
        Account -- the local account with this token or a shell account containing
        just the token and url if no local account is found
    """
    accounts = core_get_account_from_token(token, server_url)

    metrics.track(
        metrics.SDK,
        next(
            (acc for acc in accounts if acc.isDefault),
            accounts[0] if accounts else None,
        ),
        {"name": "Get Account From Token"}
    )
    return accounts
