"""
app/schemas/auth.py

Pydantic models for authentication HTTP requests.
"""

from pydantic import BaseModel


class LoginForm(BaseModel):
    identifier: str    # DNI or username
    password: str
