
from elasticsearch.client import IndicesClient
import json, codecs

class EsSchema():
    def __init__(self, client):
        self.client = client
        self.indicesClient = IndicesClient(self.client)
        self.schema = self.load_schema()

    def load_schema(self):
        with codecs.open('data/esdata.json', mode="r", encoding='UTF-8')  as file:
            return json.load(file)

    def make_index_template(self):
        if not self.indicesClient.exists_template('soaktest:template'):
            self.indicesClient.put_template("soaktest:template", self.schema['soaktest:template'])
        if not self.indicesClient.exists_template('soakdownload:template'):
            self.indicesClient.put_template("soakdownload:template", self.schema['soakdownload:template'])

    def make_kibana_index(self):
        if not self.indicesClient.exists_template("kibana_index_template:.kibana"):
            self.indicesClient.put_template("kibana_index_template:.kibana", self.schema["kibana_index_template:.kibana"])

    def make_kibana_visualization(self):
        for item in self.schema["kibana:data"]:
            self.client.index(
                index=".kibana",
                doc_type=item["_type"],
                id=item["_id"],
                body=item["_source"]
            )

    def make_schema(self):
        self.make_index_template()
        #self.make_kibana_index()
        #self.make_kibana_visualization()