import json
import os
import time
from typing import List

import boto3
from botocore.exceptions import ClientError

from source.logger import get_logger
from source.utils import get_aws_account_id

AWS_REGION = "us-east-1"

logger = get_logger(__name__)


def create_custom_blueprint(
    blueprint_name: str, session: boto3.Session = None
) -> List[str]:
    """
    Create custom blueprints from JSON schema files.

    Args:
        blueprint_name: Name of custom blueprint (without .json extension)
        session: boto3.Session object (optional, uses default if None)

    Returns:
         Blueprint ARN

    Raises:
        FileNotFoundError: If blueprint JSON file doesn't exist
        ClientError: If AWS API call fails
    """
    if session is None:
        session = boto3.Session()

    client = session.client("bedrock-data-automation")
    blueprint_path = os.path.join("data", "blueprints", f"{blueprint_name}.json")

    with open(blueprint_path) as f:
        blueprint_schema = json.load(f)

    try:
        response = client.create_blueprint(
            blueprintName=blueprint_name,
            schema=json.dumps(blueprint_schema),
            type="DOCUMENT",
        )
        arn = response["blueprint"]["blueprintArn"]
        logger.info(f"Created blueprint {blueprint_name}: {arn}")
        return arn
    except ClientError as e:
        logger.error(f"Failed to create blueprint {blueprint_name}: {e}")
        
def get_processing_results(invocation_arn: str, session=None) -> dict:
    """
    Get results from a Bedrock Data Automation job.

    Args:
        invocation_arn: ARN of the invocation to check
        session: boto3.Session object (optional, uses default if None)

    Returns:
        Job status and results

    Raises:
        ClientError: If AWS API call fails
    """
    try:
        if session is None:
            session = boto3.Session()

        client = session.client("bedrock-data-automation-runtime")
        response = client.get_data_automation_status(invocationArn=invocation_arn)
        logger.info(f"Job status: {response.get('status', 'Unknown')}")
        return response
    except ClientError as e:
        logger.error(f"Failed to get processing results: {e}")
        raise


def search_bda_project(project_name: str, session=None) -> List[dict]:
    """
    Search for BDA projects by name.

    Args:
        project_name: Name of the project to search for
        session: boto3.Session object (optional, uses default if None)

    Returns:
        List of matching projects

    Raises:
        ClientError: If AWS API call fails
    """
    if session is None:
        session = boto3.Session()

    try:
        client = session.client("bedrock-data-automation")
        response = client.list_data_automation_projects(projectStageFilter="LIVE")

        projects_arn = [
            i["projectArn"]
            for i in response["projects"]
            if i["projectName"] == project_name
        ]
        if projects_arn:
            logger.info(f"BDA project found: {projects_arn[0]}")
            return projects_arn[0]
        else:
            logger.critical(f"No BDA project found with name: {project_name}!")
            return None
    except ClientError as e:
        logger.error(f"Failed to search for projects: {e}")
        raise


def create_bda_project(
    project_name: str,
    blueprint_arns: List[str],
    stage: str = "LIVE",
    session: boto3.Session = None,
) -> str:
    """
    Create or return existing BDA project.

    Args:
        project_name: Name of the project to create
        blueprint_arns: List of blueprint ARNs to associate with project
        stage: Project stage (default: LIVE)
        session: boto3.Session object (optional, uses default if None)

    Returns:
        Project ARN

    Raises:
        ClientError: If AWS API call fails
    """

    if session is None:
        session = boto3.Session()

    if not blueprint_arns:
        raise ValueError("blueprint_arns cannot be empty")

    try:
        # Check if project exists
        client = boto3.client("bedrock-data-automation")
        projects = client.list_data_automation_projects(projectStageFilter=stage)[
            "projects"
        ]
        existing = next((p for p in projects if p["projectName"] == project_name), None)
        if existing:
            logger.info(f"Using existing project: {existing['projectArn']}")
            return existing["projectArn"]
    except ClientError as e:
        logger.error(f"Failed to list existing projects: {e}")
        raise

    try:
        # Create project
        response = client.create_data_automation_project(
            projectName=project_name,
            projectDescription="BDA Project for Well Report Extraction",
            projectStage=stage,
            standardOutputConfiguration={
                "document": {
                    "extraction": {
                        "granularity": {"types": ["DOCUMENT", "PAGE"]},
                        "boundingBox": {"state": "ENABLED"},
                    },
                    "generativeField": {"state": "ENABLED"},
                    "outputFormat": {
                        "textFormat": {"types": ["MARKDOWN"]},
                        "additionalFileFormat": {"state": "ENABLED"},
                    },
                }
            },
            customOutputConfiguration={
                "blueprints": [
                    {"blueprintArn": arn, "blueprintStage": stage}
                    for arn in blueprint_arns
                ]
            },
            overrideConfiguration={"document": {"splitter": {"state": "ENABLED"}}},
        )
        project_arn = response["projectArn"]
        logger.info(f"Created new project: {project_arn}")
        return project_arn
    except ClientError as e:
        logger.error(f"Failed to create project {project_name}: {e}")
        raise


def start_processing_job(
    project_arn: str,
    file_name: str,
    bucket_name: str,
    stage: str = "LIVE",
    wait_for_complete: bool = False,
    session: boto3.Session = None,
) -> dict:
    """
    Start async data automation processing job.

    Args:
        project_arn: ARN of the BDA project
        file_name: name of file to process
        bucket_name: S3 Bucket name for input documents and output results
        stage: Project stage (default: LIVE)
        wait_for_complete: wait for processing job to complete
        session: boto3.Session object (optional, uses default if None)

    Returns:
        Dictionary: file name and s3 URI for successfully completed jobs
        or response from invoking bda processing job

    Raises:
        ValueError: If S3 URIs are invalid
        ClientError: If AWS API call fails
    """

    try:
        if session is None:
            session = boto3.Session()

        client = session.client("bedrock-data-automation-runtime")
        aws_account_id = get_aws_account_id(session)
    except ClientError as e:
        logger.error(f"Failed to create runtime client or get account ID: {e}")
        raise

    try:
        response = client.invoke_data_automation_async(
            dataAutomationProfileArn=f"arn:aws:bedrock:{AWS_REGION}:{aws_account_id}:data-automation-profile/us.data-automation-v1",
            inputConfiguration={"s3Uri": os.path.join("s3://", bucket_name, file_name)},
            outputConfiguration={"s3Uri": os.path.join("s3://", bucket_name, "output")},
            dataAutomationConfiguration={
                "dataAutomationProjectArn": project_arn,
                "stage": stage,
            },
        )
        logger.info(
            f"Started processing job: {response.get('invocationArn', 'Unknown')}"
        )

        # -- Waiting for Status --
        if wait_for_complete:
            invocation_arn = response.get("invocationArn")
            while True:
                result = get_processing_results(invocation_arn, session)
                status = result.get("status")
                if status == "Success":
                    logger.info("Job Completed!")
                    output_s3_uri = result.get("outputConfiguration", {}).get("s3Uri")
                    logger.info(f"Job completed. Output available at: {output_s3_uri}")
                    return {"file": file_name, "S3_URI": output_s3_uri}
                logger.info(f"Job status: {status}")
                time.sleep(10)

        return response

    except ClientError as e:
        logger.error(f"Failed to start processing job: {e}")
        raise
