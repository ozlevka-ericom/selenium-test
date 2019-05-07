import os
import requests
import json


class Kibana:

    def __init__(self, kibana_host):
        if "http://" not in kibana_host and not "https://" in kibana_host:
            raise Exception("http or https protocol should be present in kibana_host")
        self.host = kibana_host

    def make_url(self, path):
        return "{0}{1}".format(self.host, path)

    def import_dashboard(self, json_path):
        url = self.make_url("/api/kibana/dashboards/import")
        with open(json_path, mode="r") as f:
            dashboard = json.load(f)
        response = requests.post(url,data=json.dumps(dashboard), headers={"kbn-xsrf": "reporting"})

        if response.status_code == 200:
            return True
        else:
            raise requests.exceptions.HTTPError(response.text)

    def export_dashboard(self, dashboard_id):
        url = self.make_url("/api/kibana/dashboards/export")
        url = url + "?dashboard={}".format(dashboard_id)
        response = requests.get(url)

        if response.status_code == 200:
            return json.loads(response.content)
        else:
            raise requests.exceptions.HTTPError(response.text)


def test_export():
    kibana = Kibana("http://192.168.50.12:5603")
    data = kibana.export_dashboard("84d2a8c0-6ca6-11e9-81cc-d35b7008c50a")
    with open("../download/dashboard.json", mode="w") as f:
        json.dump(data, f)

def test():
    kibana = Kibana("http://192.168.50.106:5601")
    kibana.import_dashboard("../download/dashboard.json")


if __name__ == "__main__":
    test_export()