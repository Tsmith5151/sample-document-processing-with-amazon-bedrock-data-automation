import json
import os
import urllib.parse
from typing import Any, Dict
from source.bda import search_bda_project, start_processing_job
from source.logger import get_logger

logger = get_logger(__name__)

# -- Get environment variables or use defaults --
BDA_PROJECT_NAME = os.environ.get("BDA_PROJECT_NAME", "energy-well-reports-bda")


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for S3 events to trigger BDA processing.

    Args:
        event: S3 event data
        context: Lambda context

    Returns:
        Response dictionary with status and results
    """
    try:

        logger.info("Received event: " + json.dumps(event, indent=2))

        # Get the object from the event and show its content type
        bucket_name = event["Records"][0]["s3"]["bucket"]["name"]
        object_key = urllib.parse.unquote_plus(
            event["Records"][0]["s3"]["object"]["key"], encoding="utf-8"
        )

        project_arn = search_bda_project(project_name=BDA_PROJECT_NAME)

        if project_arn:
            logger.info("Starting BDA Processing Job...")
            start_processing_job(
                project_arn=project_arn,
                file_name=object_key,
                bucket_name=bucket_name,
                wait_for_complete=False,
            )

            return {
                "statusCode": 200,
                "body": json.dumps(
                    {
                        "message": "BDA Processing initiated successfully",
                    }
                ),
            }
        else:
            return {
                "statusCode": 404,
                "body": json.dumps(
                    {
                        "error": "BDA Project not found",
                    }
                ),
            }
    except Exception as e:
        logger.error(f"Error processing S3 event: {str(e)}")
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
