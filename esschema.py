
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
        if not self.indicesClient.exists_template('soaktest'):
            self.indicesClient.put_template("soaktest", self.schema['template'])

    def make_kibana_index(self):
        pass

    def make_kibana_visualization(self):
        pass

    def make_schema(self):
        self.make_index_template()
        self.make_kibana_index()
        self.make_kibana_visualization()