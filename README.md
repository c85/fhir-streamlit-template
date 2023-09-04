# Streamlit SMART on FHIR Template for Cerner

## Overview

Streamlit has made the process of prototyping and developing SMART on FHIR applications incredibly straightforward, allowing you to quickly transform your ideas into live applications. This template provides a starting point for developing within the Cerner ecosystem, and includes options for both standalone and EHR launches. It also includes examples that use the following FHIR resources: Practitioner, Patient, and Observations.

## Prerequisites

- Python 3.x
- Streamlit
- Requests library
- dotenv

### Additional Requirements

- You will need to create an app registration by visiting the [Cerner Code Console](https://code-console.cerner.com/).
- If you want to test this app's functionality using the Cerner secure sandbox environment, the tenant ID for that environment is `ec2458f2-1e24-41c8-b71b-0e701af7583d`.
    - **Note**: the username and password for this sandbox environment are both `portal`.

## Setup

1. Clone this repository to your local machine.
2. Install the required Python packages:

    ```bash
    pip install -r requirements.txt
    ```

3. Create a `.env` file in the project root directory and add your Cerner configurations:

    ```env
    CERNER_CLIENT_ID=<Your_Client_ID>
    CERNER_CLIENT_SECRET=<Your_Client_Secret>
    CERNER_TENANT_ID=<Your_Tenant_ID>
    ```

4. Run the Streamlit app:

    ```bash
    streamlit run index.py
    ```

### Docker Support

This repo includes a Dockerfile for easier testing and deployment. The Dockerfile is based on Python 3.10 and sets up all the required dependencies for the app.

To build and run the Docker container, use the following commands:

```bash
docker build -t fhir-streamlit-template .
docker run -p 80:80 fhir-streamlit-template
```

### PowerChart Compatibility

The `index.html` file in the repo is a modified html file that includes the tag `<meta http-equiv="X-UA-Compatible" content="IE=edge">` after the `<head>` tag. This tag must be present in every Streamlit app that is embedded into PowerChart, otherwise it [will not load](https://fhir.cerner.com/smart/#x-ua-compatible-tag).

## How to Use

1. **Standalone Launch**: Click the "Login" button to start the standalone launch. This will redirect you to the Cerner Millennium authorization page.
2. **EHR Launch**: When the app is integrated within the EHR, it will automatically detect the EHR launch and proceed with the authorization.
3. **Resource Selection**: Use the sidebar to select the FHIR resource you want to view (Profile, Practitioner, Patient, Observation).

### Simulated EHR Launch

You can use the following URL to simulate an EHR Launch:
```
https://smart.cerner.com/smart/{TENANT_ID}/apps/{APP_ID}/?PAT_PersonId={PATIENT_ID}&username={LOGIN_ID}
```
Where:
- `TENANT_ID` is your app's tenant ID (you can use the tenant ID `ec2458f2-1e24-41c8-b71b-0e701af7583d` to run your app within Cerner's secure sandbox environment)
- `APP_ID` is the Application ID that can be found after registering your app in Cerner's Code Console
- `PATIENT_ID` is the ID of the patient you would like to provide (the template provides the ID: 12724065 as a default patient)
- `LOGIN_ID` is the username to login to the tenant (if using the Cerner secure sandbox environment the username and password is `portal`)

## Code Structure

- `get_fhir_url()` and `get_fhir_url_launch()`: Constructs the OAuth2 URL for standalone and EHR launches.
- `get_fhir_token()`: Fetches the access token using the authorization code.
- `get_practitioner()`, `get_patient()`, `get_observation()`: Fetches FHIR resources from the Cerner server.
- `main()`: The main function where Streamlit UI is constructed and all functionalities are orchestrated.

---

For more information on SMART on FHIR, please visit the [official SMART on FHIR documentation](https://docs.smarthealthit.org/).

For more information on Cerner's implementation of FHIR, please visit [Cerner's FHIR Developer Portal](https://fhir.cerner.com/).
