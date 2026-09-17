"""
Database configuration for the SaaS data pipeline.

This module contains the PostgreSQL connection settings used by the pipeline.

Important:
- Non-sensitive values may have safe local defaults.
- Sensitive values such as username and password are read from
  environment variables instead of being hard-coded in the source code.
"""

import os


# ---------------------------------------------------------------------------
# PostgreSQL connection settings
# ---------------------------------------------------------------------------

# Hostname of the machine where PostgreSQL is running.
#
# os.getenv("DB_HOST", "localhost") means:
# 1. Try to read an environment variable called DB_HOST.
# 2. If it does not exist, use "localhost" as the default value.
#
# "localhost" is appropriate for our current project because PostgreSQL
# is running locally on the same computer as the Python pipeline.
DB_HOST = os.getenv("DB_HOST", "localhost")


# Port used by PostgreSQL.
#
# Environment variables are always read as strings.
# Therefore, if DB_PORT contains "5432", we convert it to the integer 5432
# using int(...).
#
# 5432 is the standard PostgreSQL port and is used as the local default.
DB_PORT = int(os.getenv("DB_PORT", "5432"))


# Name of the PostgreSQL database that the pipeline will connect to.
#
# If the environment variable DB_NAME is not defined,
# the pipeline will use our project's database name as the default.
DB_NAME = os.getenv("DB_NAME", "saas_website_builder")


# PostgreSQL username.
#
# There is intentionally NO default value here.
# We want the actual database username to come from the environment
# instead of being fixed directly inside the Python source code.
#
# If DB_USER is not defined, the value will be None.
DB_USER = os.getenv("DB_USER")


# PostgreSQL password.
#
# The password is sensitive information, so it must NOT be written
# directly inside this file or committed to GitHub.
#
# Instead, Python will read it from an environment variable called
# DB_PASSWORD.
#
# If DB_PASSWORD is not defined, the value will be None.
DB_PASSWORD = os.getenv("DB_PASSWORD")

# ---------------------------------------------------------------------------
# Source data location
# ---------------------------------------------------------------------------

# Root directory of the canonical source-data package.
#
# This path is machine-specific, so it is provided through a
# PyCharm environment variable instead of being hard-coded here.
#
# If SOURCE_ROOT is not configured, the value will be None.
SOURCE_ROOT = os.getenv("SOURCE_ROOT")


