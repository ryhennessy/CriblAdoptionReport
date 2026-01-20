# Cribl Adoption Report

This Python script gathers deployment data from a Cribl Leader node to provide a clear picture of how Cribl is being utilized. It identifies active worker groups, routing tables, and data destinations to help stakeholders understand the flow of data from source to destination.

## Features

* Supports both **Cribl Cloud** and **On-Prem** deployments.
* Automatically discovers all active Stream Worker Groups.
* Maps Routes to their respective Pipelines and Destinations.
* Exports data into a structured CSV for easy reporting and analysis.

---

## Setup & Requirements

### Prerequisites

* **Python 3.x**
* **API Access:** A user account (on-prem) or Client Credentials (cloud) with read access to the Cribl API.

### Installation

1. Clone this repository.
2. Install the required dependencies:

```bash
pip install requests urllib3

```

---

## Usage

The script requires a command-line argument to determine the deployment type.

### 1. Command-Line Arguments

Run the script by specifying one of the following two options:

```bash
# For On-Premise deployments
python3 main.py onprem

# For Cribl Cloud deployments
python3 main.py cloud

```

### 2. Interactive Prompts

Based on the argument provided, the script will prompt for the following credentials:

| Deployment | Required Input | Format / Note |
| --- | --- | --- |
| **On-Prem** | Cribl Leader URL | `https://leader.example.com:9000` |
|  | Username | Standard UI login name |
|  | Password | Masked input via `getpass` |
| **Cloud** | Cloud URL | `https://<workspace>-<orgId>.cribl.cloud` |
|  | Client ID | Found in Cloud Organization settings |
|  | Client Secret | Found in Cloud Organization settings |

---

## Output

Upon successful execution, the script generates a file named **`dataflow.csv`** in the local directory. The CSV contains the following columns:

* **Worker Group:** The name of the group processing the data.
* **Route Name:** The specific route defined in the routing table.
* **Filter:** The filter criteria used to catch the data.
* **Pipeline:** The pipeline associated with the route.
* **Destination Name:** The ID of the output destination.
* **Destination Type:** The specific type of destination (e.g., `splunk`, `s3`, `elastic`).

---

## Troubleshooting

* **Invalid Connection String:** Ensure you include the protocol (`https://`) and the correct port (default is `9000`) for on-premise deployments.
* **Login Failed:** * **On-Prem:** Verify that your username and password are correct and that the user has API permissions.
* **Cloud:** Double-check that your Client ID and Client Secret are active and have the "Cribl Admin" or "Read-only" role assigned.

* **SSL Warnings:** The script is configured to bypass SSL verification for on-premise environments with self-signed certificates. You may see a brief warning in the console, but the script will continue to run.
* **No Worker Groups Found:** Ensure the account used has permission to view worker groups at the Leader/Org level.

---

## Author

**Ryan Hennessy** – [rhennessy@cribl.io](mailto:rhennessy@cribl.io)
