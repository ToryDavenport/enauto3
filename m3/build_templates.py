#!/usr/bin/env python

"""
Author: Nick Russo
Purpose: Demonstrate how to use the template programmer tool on
Cisco DNA center via API calls.
"""

import os
import json
from dnac_requester import DNACRequester


def main():
    """
    Execution begins here.
    """

    # Create a DNARequester object with our sandbox parameters
    dnac = DNACRequester(
        host="dnac.njrusmc.net",
        username="nickrus",
        password="Cisco123!",
        verify=False,
        old_style=True,
        # host="10.10.20.85", username="admin", password="Cisco1234!", verify=False
    )

    # Build a new project using a name and description
    proj_body = {
        "name": "globo_proj",
        "description": "testing some python scripts",
    }
    proj_resp = dnac.req(
        f"dna/intent/api/v1/template-programmer/project",
        method="post",
        jsonbody=proj_body,
    )

    # Wait for the project to get completed, then extract the project ID
    proj_task = dnac.wait_for_task(proj_resp.json()["response"]["taskId"])
    proj_id = proj_task.json()["response"]["data"]

    # Load in the various template bodies, then create a template based on each
    for template in os.listdir("templates"):
        with open(f"templates/{template}", "r") as handle:
            temp_data = json.load(handle)
        temp_resp = dnac.req(
            f"dna/intent/api/v1/template-programmer/project/{proj_id}/template",
            method="post",
            jsonbody=temp_data["body"],
        )

        # Wait for task to finish, and capture the "data" value, which is
        # the template ID
        temp_task = dnac.wait_for_task(temp_resp.json()["response"]["taskId"])
        temp_id = temp_task.json()["response"]["data"]

        # Start a simulation (aka preview) to render the template. First,
        # build the body by combining the sample variables and template ID
        prev_body = {"params": temp_data["params"], "templateId": temp_id}

        # Then, issue the HTTP PUT request to begin the previous without
        # raising an HTTPError if the status code >= 400
        prev_resp = dnac.req(
            "dna/intent/api/v1/template-programmer/template/preview",
            method="put",
            jsonbody=prev_body,
        )
        prev_data = prev_resp.json()

        # If any validation errors exist, print them out. These include using
        # the wrong data type, omitted required variables, wrong template IDs,
        # and more
        print(f"\nChecking template {template}:")
        if prev_data["validationErrors"]:
            print(f"Errors:")
            for error in prev_data["validationErrors"]:
                print(f"{error['type']}: {error['message']}")

        # The simulation succeeded, so print the rendered text after
        # variable substitution has taken place
        else:
            print(f"Snippet rendered:")
            print(prev_data["cliPreview"])

            # Uncomment to apply the template on a test Cat9300 switch
            version_and_deploy(dnac, temp_data, temp_id)


def version_and_deploy(dnac, temp_data, temp_id, ip_addr="100.118.1.69"):
    """
    Helper function to version and deploy the templates as they are rendered.
    This should only be called when the template renders successfully (ie,
    without errors). This issues the "version" and "deploy" API calls to
    a sample IP address specified.
    """

    # Version (commit) template. You must do this before trying to deploy
    # the template
    ver_body = {"comments": "initial commit via API", "templateId": temp_id}
    ver_resp = dnac.req(
        "dna/intent/api/v1/template-programmer/template/version",
        method="post",
        jsonbody=ver_body,
    )
    ver_task = dnac.wait_for_task(ver_resp.json()["response"]["taskId"])
    print(f"Version status: {ver_task.json()['response']['progress']}")

    # Deploy (apply) template. The body is similar to the preview body
    # except we must specify targets to configure. This is a list of
    # dictionaries, allowing for bulk deployment. To keep it simple,
    # you can hardcode a single IP address or UUID into the "id" field
    deploy_body = {
        "forcePushTemplate": False,
        "targetInfo": [
            {
                "id": ip_addr,
                "params": temp_data["params"],
                "type": "MANAGED_DEVICE_IP",
            }
        ],
        "templateId": temp_id,
    }
    deploy_resp = dnac.req(
        "dna/intent/api/v1/template-programmer/template/deploy",
        method="post",
        jsonbody=deploy_body,
    )
    print(f"Deploy status: {deploy_resp.json()['deploymentId']}")


if __name__ == "__main__":
    main()
