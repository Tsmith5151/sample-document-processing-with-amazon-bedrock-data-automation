# Energy Well Reports Processing with Amazon Bedrock Data Automation

This project demonstrates how to leverage Amazon Bedrock Data Automation to extract insights from energy well reports and operational documents. The solution provides a comprehensive walkthrough notebook and utility functions to help jumpstart processing various document types commonly found in the energy sector.

## Overview

The energy industry generates large volumes of unstructured documents such as well permits, petrophysical logs, directional surveys, bit reports, frack data, and regulatory filings. This project shows how to use Amazon Bedrock Data Automation to automate extracting key insights from technical documentation. 

## Project Structure

```
23-Energy-Well-Reports/
├── 23-Energy_Well_Reports.ipynb          # Interactive walkthrough notebook
├── data/                                 # Sample data and configurations
│   ├── blueprints/                       # Custom extraction blueprints
│   │   ├── operator1_engineering_blueprint.json
│   │   └── operator2_engineering_blueprint.json
│   └── reports/                          # Sample well reports (PDF)
│       ├── operator1_report.pdf
│       └── operator2_report.pdf
├── source/                               # Helper utility functions
│   ├── bda.py                            # Bedrock Data Automation utilities
│   ├── logger.py                         # Logging configuration
│   └── utils.py                          # AWS and data processing utilities
└── README.md                           
```

## Key Features

### Utility Functions

The `source/utils.py` module provides essential functions for:

- **AWS Integration**: Get account ID and manage AWS sessions
- **S3 Operations**: Upload documents, list files, and download results
- **Data Processing**: Convert inference results to DataFrames
- **Custom Output Handling**: Extract and process custom blueprint outputs

### Sample Documents

The project includes sample well reports from different operators to demonstrate:
- Processing documents with varying formats and structures
- Creating operator-specific extraction blueprints
- Handling multimodal content (text, tables, diagrams)

## Getting Started

1. **Prerequisites**:
   - AWS account with Bedrock Data Automation access
   - Python environment with required dependencies
   - S3 bucket for document storage and processing

2. **Setup**:
   - Clone this repository
   - Configure AWS credentials
   - Install required Python packages 
      - boto3>=1.38.27 
      - pandas>=2.3.1
      - s3fs==2025.5.1

3. **Run the Notebook**:
   - Open `23-Energy_Well_Reports.ipynb`
   - Follow the step-by-step walkthrough
   - Experiment with the sample documents and blueprints
