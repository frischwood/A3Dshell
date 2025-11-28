"""
Embedded templates for A3Dshell web version.

This module provides embedded template content with optional file override capability.
Templates are embedded as Python constants to eliminate external file dependencies
for the web-hosted frontend version.
"""

from .embedded import get_template, TEMPLATES, LUS_SNO_TEMPLATES

__all__ = ['get_template', 'TEMPLATES', 'LUS_SNO_TEMPLATES']
