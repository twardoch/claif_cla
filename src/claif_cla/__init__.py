# this_file: claif_cla/src/claif_cla/__init__.py
"""Claif provider for Anthropic Claude with OpenAI Responses API compatibility."""

from claif_cla.__version__ import __version__
from claif_cla.client import ClaudeClient

__all__ = ["ClaudeClient", "__version__"]
