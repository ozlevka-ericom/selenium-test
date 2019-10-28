import consul
import os
import json
import sys 

consul_host = "localhost"
if "CONSUL_HOST" in os.environ:
    consul_host = os.environ["CONSUL_HOST"]

consul_port = "8500"
if "CONSUL_PORT" in os.environ:
    consul_port = os.environ["CONSUL_PORT"]


client = consul.Consul(host=consul_host, port=consul_port)

def set_policy(white=1):
    policies = client.kv.get("policies/override_policies", recurse=True)
    if policies[1] is not None:
        value = json.loads(policies[1][0]['Value'])
        
        value[0]['access'] = int(white)
        client.kv.put("policies/override_policies", json.dumps(value))

def main(args):
    if len(args) > 1:
        set_policy(args[1])
    else:
        print("No policy value sent")
    


if __name__ == "__main__":
    main(sys.argv)