#!/usr/bin/env python

"""
Author: Nick Russo
Purpose: Demonstrate how to use the path trace tool on
Cisco DNA center via API calls.
"""

from dnac_requester import DNACRequester


def main():
    """
    Execution begins here.
    """

    # Create a DNARequester object with our sandbox parameters
    dnac = DNACRequester(
        # host="sandboxdnac2.cisco.com", username="devnetuser", password="Cisco123!", verify=False
        host="10.10.20.85",
        username="admin",
        password="Cisco1234!",
        verify=False,
    )

    # path = dnac.req( f"dna/intent/api/v1/flow-analysis",)
    # print(json.dumps(path.json(), indent=2))

    body = {
        "sourceIP": "10.10.20.81",
        "destIP": "10.10.20.82",
        "inclusions": ["INTERFACE-STATS", "DEVICE-STATS", "QOS-STATS"],
        "controlPath": False,
        "periodicRefresh": False,
    }
    path = dnac.req("dna/intent/api/v1/flow-analysis", method="post", jsonbody=body)
    # print(json.dumps(path.json(), indent=2))

    path_data = path.json()["response"]
    task_resp = dnac.wait_for_task(path_data["taskId"])
    if task_resp.json()["response"]["progress"] != path_data["flowAnalysisId"]:
        raise ValueError("Unexpected error; task progress doesn't match flow id")
    # print(json.dumps(task_resp.json(), indent=2))

    flow_resp = dnac.req(
        f"dna/intent/api/v1/flow-analysis/{path_data['flowAnalysisId']}"
    )
    # print(json.dumps(flow_resp.json(), indent=2))

    flow_data = flow_resp.json()["response"]
    print(
        f"Path trace {flow_data['request']['sourceIP']}->{flow_data['request']['destIP']}"
    )
    for i, hop in enumerate(flow_data["networkElementsInfo"]):
        print(f"Hop {i+1}: {hop['name']}")


if __name__ == "__main__":
    main()
