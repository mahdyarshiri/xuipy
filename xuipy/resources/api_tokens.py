from xuipy.exceptions import XUIValidationError


class ApiTokens:
    """API token management methods."""

    def get_api_tokens(self):
        """List every API token, enabled or not. The token value itself is never returned, only metadata."""
        return self._request("GET", "/panel/api/setting/apiTokens", error_msg="Failed to get API tokens")

    def create_api_token(self, name: str):
        """Mint a new API token."""
        if not (1 <= len(name) <= 64):
            raise XUIValidationError("Token name must be between 1 and 64 characters")
        return self._request("POST", "/panel/api/setting/apiTokens/create", json_data={"name": name}, error_msg="Failed to create API token")

    def delete_api_token(self, token_id: int):
        """Permanently delete a token. Any caller using it stops authenticating immediately."""
        return self._request("POST", f"/panel/api/setting/apiTokens/delete/{token_id}", error_msg=f"Failed to delete API token {token_id}")

    def set_api_token_enabled(self, token_id: int, enabled: bool):
        """Toggle a token enabled/disabled without deleting it."""
        return self._request("POST", f"/panel/api/setting/apiTokens/setEnabled/{token_id}", json_data={"enabled": enabled}, error_msg=f"Failed to set enabled on API token {token_id}")