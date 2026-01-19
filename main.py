#!/usr/bin/python3

import sys
import os
import requests
import getpass
import csv

# import datetime
import urllib3
# from requests.exceptions import RequestException

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
        "Provide Cloud URL (Format of https://<workspaceName>.<organizationId>.cribl.cloud): "
    )
    loginData["client_id"] = input("Enter Client ID: ")
    loginData["client_secret"] = input("Enter Client Secret (Will not echo out): ")

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


# import csv
#
# data_dict = [
#     {"Name": "John", "Age": "25", "Country": "USA"},
#     {"Name": "Sarah", "Age": "30", "Country": "Canada"}
# ]
# fieldnames = ["Name", "Age", "Country"]
#
# with open('output_dict.csv', 'w', newline='') as file:
#     writer = csv.DictWriter(file, fieldnames=fieldnames)
#     writer.writeheader() # Write the header row
#     writer.writerows(data_dict) # Write the data rows


def writeRoutes(criblHeaders, criblWorkerGroups, criblUrl):
    fieldnames = ["name", "filter", "pipeline", "output", "description"]
    with open("routes.csv", "a", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        if os.stat("routes.csv").st_size == 0:
            writer.writeheader()
        for workerGroup in criblWorkerGroups:
            routeUrl = f"{criblUrl}/api/v1/m/{workerGroup}/routes"
            resp = requests.get(routeUrl, headers=criblHeaders)
            if resp.status_code == 200:
                resp = resp.json()
                for route in resp:
                    writer.writerow(route)
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
    print(criblWorkerGroups)
    print(f"AuthToken: {criblToken}")
    # writeRoutes(criblHeaders, criblWorkerGroups, criblUrl)


if __name__ == "__main__":
    main()
