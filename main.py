###
# Script for gathering basic data flow information from a Cribl leader node.
# This script expects one of two options as a command line argument (cloud or onprem).
# Based on the command line argument provided the script will then prompt the user for
# all the required information to login to that Cribl environment.
# The script then query the Cribl Leader API for infomration about the routing tables
# across all the different worker groups.
# The output is a CSV with basic information about data flows through the different
# worker groups
#
# For more infomration: https://github.com/ryhennessy/CriblAdoptionReport
# Author: Ryan Hennessy (rhennessy@cribl.io)
###


#!/usr/bin/python3

import sys
import requests
import getpass
import urllib3

# Added to remove any warning messages from urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def onpremLogin(criblHeaders):
    loginData = {}
    criblUrl = input("Cribl Leader URL (https://leader.examle.com:9000): ").rstrip()
    loginData["username"] = input("Login: ").rstrip()
    loginData["password"] = getpass.getpass("Password: ")
    criblAuthUrl = f"{criblUrl}/api/v1/auth/login"

    try:
        resp = requests.post(
            criblAuthUrl, json=loginData, headers=criblHeaders, verify=False
        )
        return resp.json()["token"], criblUrl
    except (requests.exceptions.ConnectionError, requests.exceptions.MissingSchema):
        print("\nInvalid connection string. Verify hostname, port, and protocol.")
        sys.exit(1)
    except:
        print("\nLogin Failed")
        print("-" * 25)
        print(str(resp.status_code) + " " + resp.text)
        sys.exit(1)


def cloudLogin(criblHeaders):
    loginData = {}
    criblAuthUrl = "https://login.cribl.cloud/oauth/token"

    loginData["audience"] = "https://api.cribl.cloud"
    loginData["grant_type"] = "client_credentials"
    criblUrl = input(
        "Provide Cloud URL (Format of https://<workspaceName>-<organizationId>.cribl.cloud): "
    )
    loginData["client_id"] = input("Enter Client ID: ")
    loginData["client_secret"] = getpass.getpass("Enter Client Secret: ")

    try:
        resp = requests.post(criblAuthUrl, json=loginData, headers=criblHeaders)
        return resp.json()["access_token"], criblUrl
    except:
        print("\nLogin Failed")
        print("-" * 25)
        print(str(resp.status_code) + " " + resp.text)
        sys.exit(1)


def getWorkerGroups(criblHeaders, criblUrl):
    criblWorkerGroups = []
    criblWGUrl = f"{criblUrl}/api/v1/master/groups"
    resp = requests.get(criblWGUrl, headers=criblHeaders)

    if resp.status_code == 200:
        resp = resp.json()
        for wg in resp["items"]:
            if "isFleet" not in wg or not wg["isFleet"]:
                if "isSearch" not in wg or not wg["isSearch"]:
                    criblWorkerGroups.append(wg["id"])
        return criblWorkerGroups
    else:
        print("Unable to get Worker Groups")
        sys.exit(1)


def getSources(criblHeaders, criblWorkerGroups, criblUrl):
    filteredSourceList = []
    for workerGroup in criblWorkerGroups:
        sourceUrl = f"{criblUrl}/api/v1/m/{workerGroup}/system/inputs"
        resp = requests.get(sourceUrl, headers=criblHeaders)
        if resp.status_code == 200:
            for source in resp.json()["items"]:
                if "connections" in source:
                    for connection in source["connections"]:
                        if "pipeline" not in connection:
                            criblPipeline = "passthru"
                        else:
                            criblPipeline = connection["pipeline"]
                        criblDestination = connection["output"]
                        filteredSourceList.append(
                            {
                                "name": source["id"],
                                "type": source["type"],
                                "workergroup": workerGroup,
                                "pipeline": criblPipeline,
                                "output": criblDestination,
                            }
                        )
    return filteredSourceList


def getDestinations(criblHeaders, criblWorkerGroups, criblUrl):
    fullDestinationList = {}
    for workerGroup in criblWorkerGroups:
        destUrl = f"{criblUrl}/api/v1/m/{workerGroup}/system/outputs"
        resp = requests.get(destUrl, headers=criblHeaders)
        fullDestinationList[workerGroup] = {}
        if resp.status_code == 200:
            for dest in resp.json()["items"]:
                destName = dest["id"]
                destType = dest["type"]
                fullDestinationList[workerGroup][destName] = destType
    return fullDestinationList


def getRoutes(criblHeaders, criblWorkerGroups, criblUrl):
    fullRouteList = {}
    for workerGroup in criblWorkerGroups:
        routeUrl = f"{criblUrl}/api/v1/m/{workerGroup}/routes"
        resp = requests.get(routeUrl, headers=criblHeaders)
        if resp.status_code == 200:
            fullRouteList[workerGroup] = resp.json()["items"][0]["routes"]
    return fullRouteList


def writeCSV(fullRouteList, fullDestinationList, fullQCList):
    with open(
        "dataflow.csv",
        "w",
    ) as csv:
        csv.write(
            "Worker Group, Route Name, Filter, Pipeline, Destination Name, Destination Type"
        )
        for workerGroup in fullRouteList:
            for route in fullRouteList[workerGroup]:
                if "disabled" in route and not route["disabled"]:
                    destType = fullDestinationList[workerGroup][route["output"]]
                    csv.write(
                        f"\n{workerGroup},{route['name']},{route['filter']},{route['pipeline']},{route['output']},{destType}"
                    )
        for quickConnect in fullQCList:
            csv.write(
                f"\n{quickConnect['workergroup']},Quick Connect,{quickConnect['name']}:{quickConnect['type']},{quickConnect['pipeline']},{quickConnect['output']},Validate Destination Type"
            )
    return


def main():
    criblHeaders = {"Content-type": "application/json", "Accept": "application/json"}

    if len(sys.argv) == 1:
        print("Please specifiy a Cribl Deployment type either 'cloud' or 'onprem'")
        sys.exit(1)

    if sys.argv[1].lower() == "cloud":
        criblToken, criblUrl = cloudLogin(criblHeaders)
    elif sys.argv[1].lower() == "onprem":
        criblToken, criblUrl = onpremLogin(criblHeaders)
    else:
        print("Please specifiy a Cribl Deployment type either 'cloud' or 'onprem'")
        sys.exit(1)

    criblHeaders["Authorization"] = "Bearer " + criblToken

    criblWorkerGroups = getWorkerGroups(criblHeaders, criblUrl)
    fullDestinationList = getDestinations(criblHeaders, criblWorkerGroups, criblUrl)
    fullRouteList = getRoutes(criblHeaders, criblWorkerGroups, criblUrl)
    fullQCList = getSources(criblHeaders, criblWorkerGroups, criblUrl)
    writeCSV(fullRouteList, fullDestinationList, fullQCList)
    print("Wrote output file dataflow.csv")


if __name__ == "__main__":
    main()
