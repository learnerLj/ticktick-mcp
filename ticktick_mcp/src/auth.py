"""
TickTick OAuth authentication module.

This module handles the OAuth 2.0 flow for authenticating with TickTick,
allowing users to authorize the application and obtain access tokens
without manually copying and pasting tokens.
"""

import base64
import http.server
import logging
import os
import socketserver
import time
import urllib.parse
import webbrowser
from pathlib import Path
from typing import Optional

import requests
from dotenv import load_dotenv

from ..config import ConfigManager

# Set up logging
logger = logging.getLogger(__name__)

# Default scopes for TickTick API
DEFAULT_SCOPES = ["tasks:read", "tasks:write"]


class OAuthCallbackHandler(http.server.BaseHTTPRequestHandler):
    """Handle OAuth callback requests."""

    # Class variable to store the authorization code
    auth_code = None

    def do_GET(self):
        """Handle GET requests to the callback URL."""
        # Parse query parameters
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)

        if "code" in params:
            # Store the authorization code
            OAuthCallbackHandler.auth_code = params["code"][0]

            # Send success response
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()

            # Return a nice HTML page
            response = """
            <html>
            <head>
                <title>TickTick MCP Server - Authentication Successful</title>
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        line-height: 1.6;
                        max-width: 600px;
                        margin: 0 auto;
                        padding: 20px;
                        text-align: center;
                    }
                    h1 {
                        color: #4CAF50;
                    }
                    .box {
                        border: 1px solid #ddd;
                        border-radius: 5px;
                        padding: 20px;
                        margin-top: 20px;
                        background-color: #f9f9f9;
                    }
                </style>
            </head>
            <body>
                <h1>Authentication Successful!</h1>
                <div class="box">
                    <p>You have successfully authenticated with TickTick.</p>
                    <p>You can now close this window and return to the terminal.</p>
                </div>
            </body>
            </html>
            """
            self.wfile.write(response.encode())
        else:
            # Send error response
            self.send_response(400)
            self.send_header("Content-type", "text/html")
            self.end_headers()

            response = """
            <html>
            <head>
                <title>TickTick MCP Server - Authentication Failed</title>
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        line-height: 1.6;
                        max-width: 600px;
                        margin: 0 auto;
                        padding: 20px;
                        text-align: center;
                    }
                    h1 {
                        color: #f44336;
                    }
                    .box {
                        border: 1px solid #ddd;
                        border-radius: 5px;
                        padding: 20px;
                        margin-top: 20px;
                        background-color: #f9f9f9;
                    }
                </style>
            </head>
            <body>
                <h1>Authentication Failed</h1>
                <div class="box">
                    <p>Failed to receive authorization code from TickTick.</p>
                    <p>Please try again or check the error message in the terminal.</p>
                </div>
            </body>
            </html>
            """
            self.wfile.write(response.encode())

    def log_message(self, format, *args):
        """Override to prevent noisy logging to stderr."""
        pass


class TickTickAuth:
    """TickTick OAuth authentication manager."""

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        redirect_uri: str = "http://localhost:8000/callback",
        port: int = 8000,
        config_manager: Optional[ConfigManager] = None,
    ):
        """
        Initialize the TickTick authentication manager.

        Args:
            client_id: The TickTick client ID
            client_secret: The TickTick client secret
            redirect_uri: The redirect URI for OAuth callbacks
            port: The port to use for the callback server
            config_manager: ConfigManager instance for loading/saving config
        """
        self.config_manager = config_manager or ConfigManager()
        
        # Try to load from config if credentials not provided
        if client_id and client_secret:
            self.client_id = client_id
            self.client_secret = client_secret
            # Save credentials to config
            self._save_credentials(client_id, client_secret)
        else:
            try:
                config = self.config_manager.load_config()
                self.client_id = config.client_id
                self.client_secret = config.client_secret
            except Exception:
                self.client_id = None
                self.client_secret = None

        self.auth_url = "https://ticktick.com/oauth/authorize"
        self.token_url = "https://ticktick.com/oauth/token"
        self.redirect_uri = redirect_uri
        self.port = port
        self.auth_code = None
        self.tokens = None

        # Check if credentials are available
        if not self.client_id or not self.client_secret:
            logger.warning(
                "TickTick client ID or client secret is missing. "
                "Please provide them as parameters or configure them first."
            )

    def get_authorization_url(self, scopes: list = None, state: str = None) -> str:
        """
        Generate the TickTick authorization URL.

        Args:
            scopes: List of OAuth scopes to request
            state: State parameter for CSRF protection

        Returns:
            The authorization URL
        """
        if not scopes:
            scopes = DEFAULT_SCOPES

        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": " ".join(scopes),
        }

        if state:
            params["state"] = state

        # Build the URL with query parameters
        query_string = urllib.parse.urlencode(params)
        return f"{self.auth_url}?{query_string}"

    def start_auth_flow(self, scopes: list = None) -> str:
        """
        Start the OAuth flow by opening the browser and waiting for the callback.

        Args:
            scopes: List of OAuth scopes to request

        Returns:
            The obtained access token or an error message
        """
        if not self.client_id or not self.client_secret:
            return "TickTick client ID or client secret is missing. Please set up your credentials first."

        # Generate a random state parameter for CSRF protection
        state = base64.urlsafe_b64encode(os.urandom(30)).decode("utf-8")

        # Get the authorization URL
        auth_url = self.get_authorization_url(scopes, state)

        print("Opening browser for TickTick authorization...")
        print("If the browser doesn't open automatically, please visit this URL:")
        print(auth_url)

        # Open the browser for the user to authorize
        webbrowser.open(auth_url)

        # Start a local server to handle the OAuth callback
        httpd = None
        try:
            # Use a socket server to handle the callback
            OAuthCallbackHandler.auth_code = None
            httpd = socketserver.TCPServer(("", self.port), OAuthCallbackHandler)

            print(f"Waiting for authentication callback on port {self.port}...")

            # Run the server until we get the authorization code
            # Set a timeout for the server
            timeout = 300  # 5 minutes
            start_time = time.time()

            while not OAuthCallbackHandler.auth_code:
                # Handle one request with a short timeout
                httpd.timeout = 1.0
                httpd.handle_request()

                # Check if we've timed out
                if time.time() - start_time > timeout:
                    return "Authentication timed out. Please try again."

            # Store the auth code
            self.auth_code = OAuthCallbackHandler.auth_code

            # Exchange the code for tokens
            return self.exchange_code_for_token()

        except Exception as e:
            logger.error(f"Error during OAuth flow: {e}")
            return f"Error during OAuth flow: {str(e)}"
        finally:
            # Clean up the server
            if httpd:
                httpd.server_close()

    def exchange_code_for_token(self) -> str:
        """
        Exchange the authorization code for an access token.

        Returns:
            Success message or error message
        """
        if not self.auth_code:
            return "No authorization code available. Please start the authentication flow again."

        # Prepare the token request
        token_data = {
            "grant_type": "authorization_code",
            "code": self.auth_code,
            "redirect_uri": self.redirect_uri,
            "scope": " ".join(DEFAULT_SCOPES),
        }

        # Prepare Basic Auth credentials
        auth_str = f"{self.client_id}:{self.client_secret}"
        auth_bytes = auth_str.encode("ascii")
        auth_b64 = base64.b64encode(auth_bytes).decode("ascii")

        headers = {
            "Authorization": f"Basic {auth_b64}",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept-Encoding": None,
            "User-Agent": "curl/8.7.1",
        }

        try:
            # Send the token request
            response = requests.post(self.token_url, data=token_data, headers=headers)
            response.raise_for_status()

            # Parse the response
            self.tokens = response.json()

            # Save the tokens to config
            self._save_tokens()

            return "Authentication successful! Access token saved to configuration."

        except requests.exceptions.RequestException as e:
            logger.error(f"Error exchanging code for token: {e}")
            if hasattr(e, "response") and e.response is not None:
                try:
                    error_details = e.response.json()
                    return f"Error exchanging code for token: {error_details}"
                except:
                    return f"Error exchanging code for token: {e.response.text}"
            return f"Error exchanging code for token: {str(e)}"

    def _save_tokens(self) -> None:
        """Save the tokens using ConfigManager."""
        if not self.tokens:
            return

        access_token = self.tokens.get("access_token", "")
        refresh_token = self.tokens.get("refresh_token")
        
        self.config_manager.save_tokens(access_token, refresh_token)
        logger.info("Tokens saved to configuration")

    def _save_credentials(self, client_id: str, client_secret: str) -> None:
        """Save client credentials to config file."""
        # Load existing config content to preserve other settings
        config_content = {}
        if self.config_manager.env_file.exists():
            with open(self.config_manager.env_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        config_content[key] = value

        # Update credentials
        config_content["TICKTICK_CLIENT_ID"] = client_id
        config_content["TICKTICK_CLIENT_SECRET"] = client_secret

        # Write back to config file
        with open(self.config_manager.env_file, "w") as f:
            for key, value in config_content.items():
                f.write(f"{key}={value}\n")

        logger.info("Credentials saved to configuration")


def setup_auth_cli():
    """Run the authentication flow as a CLI utility."""
    import argparse

    parser = argparse.ArgumentParser(description="TickTick OAuth Authentication")
    parser.add_argument("--client-id", help="TickTick client ID")
    parser.add_argument("--client-secret", help="TickTick client secret")
    parser.add_argument(
        "--redirect-uri",
        default="http://localhost:8000/callback",
        help="OAuth redirect URI",
    )
    parser.add_argument(
        "--port", type=int, default=8000, help="Port to use for OAuth callback server"
    )
    parser.add_argument("--env-file", help="Path to .env file with credentials")

    args = parser.parse_args()

    auth = TickTickAuth(
        client_id=args.client_id,
        client_secret=args.client_secret,
        redirect_uri=args.redirect_uri,
        port=args.port,
        env_file=args.env_file,
    )

    result = auth.start_auth_flow()
    print(result)


if __name__ == "__main__":
    setup_auth_cli()
