"""Shared FastMCP server instance.

Every tool module imports ``mcp`` from here and registers its tools via
``@mcp.tool(...)``. ``server.py`` triggers registration by importing each
tool module, then calls ``mcp.run()``.
"""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("productive")
