import json
import logging
import time

import boto3
from botocore.exceptions import ClientError
from fastapi import FastAPI, HTTPException


# --------------------------------------------------
# Logging
# --------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[
        logging.FileHandler("/var/log/fastapi/app.log"),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger("fastapi-lab")


# --------------------------------------------------
# AWS clients
# --------------------------------------------------

secrets_client = boto3.client("secretsmanager", region_name="eu-north-1")
ssm_client = boto3.client("ssm", region_name="eu-north-1")


# --------------------------------------------------
# FastAPI
# --------------------------------------------------

app = FastAPI(title="AWS Secrets & Parameter Store Lab")


# --------------------------------------------------
# Basic endpoints
# --------------------------------------------------

@app.get("/")
def root():
    logger.info("Root endpoint called")

    return {
        "message": "FastAPI AWS lab is running"
    }


@app.get("/health")
def health():
    logger.info("Health check called")

    return {
        "status": "healthy"
    }


# --------------------------------------------------
# Parameter Store
# --------------------------------------------------

@app.get("/config")
def get_config():
    logger.info("Reading application configuration from Parameter Store")

    try:
        environment = ssm_client.get_parameter(
            Name="/fastapi-lab/environment"
        )["Parameter"]["Value"]

        api_version = ssm_client.get_parameter(
            Name="/fastapi-lab/api_version"
        )["Parameter"]["Value"]

        log_level = ssm_client.get_parameter(
            Name="/fastapi-lab/log_level"
        )["Parameter"]["Value"]

        logger.info("Successfully retrieved application configuration")

        return {
            "environment": environment,
            "api_version": api_version,
            "log_level": log_level,
        }

    except ClientError:
        logger.exception("Failed to retrieve parameters")

        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve configuration",
        )


# --------------------------------------------------
# Secrets Manager
# --------------------------------------------------

@app.get("/secret-status")
def secret_status():
    logger.info("Reading secret from Secrets Manager")

    try:
        response = secrets_client.get_secret_value(
            SecretId="fastapi-lab/database"
        )

        secret = json.loads(response["SecretString"])

        logger.info(
            "Successfully retrieved database secret"
        )

        # IMPORTANT:
        # Never return the password itself.
        return {
            "secret_loaded": True,
            "username": secret["username"],
            "password_loaded": "password" in secret,
        }

    except ClientError:
        logger.exception(
            "Failed to retrieve secret from Secrets Manager"
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve secret",
        )


# --------------------------------------------------
# Simulate application error
# --------------------------------------------------

@app.get("/error")
def error():
    logger.error("Intentional test error triggered")

    raise HTTPException(
        status_code=500,
        detail="Intentional test error",
    )


# --------------------------------------------------
# Simulate slow request
# --------------------------------------------------

@app.get("/slow")
def slow():
    logger.info("Slow endpoint started")

    time.sleep(5)

    logger.info("Slow endpoint finished")

    return {
        "message": "Request took approximately 5 seconds"
    }
