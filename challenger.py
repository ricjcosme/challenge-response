# -*- coding: utf-8 -*-

import ed25519
import base64
import base58
import requests
import random
import string
import sys
import json
import re
import time
from multiprocessing import Pool
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs

if len(sys.argv[1:]) < 1:
    sys.exit("Need challengee's DID")
challengee_did = str(sys.argv[1:][0])

# universal resolver is converting array to objects when only one item is found
# using dominode's resolver to standards enforce standards definition
pattern = re.compile("^did:dom:[a-km-zA-HJ-NP-Z1-9]{30,30}$")
if not pattern.match(challengee_did):
    sys.exit("Invalid DID provided")
universal_resolver_addr = "https://did-resolver.dominode.com/ddo/"
print("Got challengee DID: %s" % challengee_did)


# signature verification function
def verify(challenge, sig, pubkey):
    verifying_key = ed25519.VerifyingKey(base64.b64encode(base58.b58decode(pubkey)),
                                         encoding="base64")
    verifying_key.verify(json.loads(sig)["payload"],
                         challenge.encode("ascii"),
                         encoding="hex")


# base http server handler class for callback
class MyHttpHandler(BaseHTTPRequestHandler):

    challenge = ""
    pubkey = ""
    callback_id = ""

    def do_POST(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        if callback_id != self.path.split("?")[1]:
            self.wfile.write(b"Unknown callback handle")
            sys.exit("Unknown callback handle")
        try:
            content_len = int(self.headers.get('content-length', 0))
            post_body = self.rfile.read(content_len)
            verify(challenge, post_body, pubkey)
            # Send the html message
            self.wfile.write(b"Valid sig")
            sys.exit("Challengee's DID %s is legit!!" % challengee_did)
        except Exception:
            self.wfile.write(b"Invalid sig")
            sys.exit("Challengee's DID %s is NOT legit!!" % challengee_did)
        return

    def log_message(self, format, *args):
        return


def callback_http(s):
    s.serve_forever()


# challenge generation function
def id_generator(size=32, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


# STEP 1: generate random content for challenge
challenge = id_generator()
print("Generated challenge content: %s" % challenge)

# STEP 2: start callback, send challenge request
# and verify returned signature via callback HTTP server
try:

    # get DID document
    did_req = requests.get(universal_resolver_addr + challengee_did)

    # parse and validate DidAuthService endpoint and Authentication public key
    json_did_doc = did_req.json()
    endpoint = [x for x in json_did_doc["service"] if x["type"] == "DidAuthService"][0]["serviceEndpoint"]
    print("Challengee's DidAuthService endpoint: %s" % endpoint)
    pubKey_identifier = [x for x in json_did_doc["authentication"]][0]["publicKey"]
    pubkey = [x for x in json_did_doc["publicKey"] if x["id"] == pubKey_identifier][0]["publicKeyBase58"]
    print("Challengee's PublicKey: %s" % pubkey)
    # generate callback handle id
    callback_id = id_generator()
    challenge_data = {"payload": challenge, "callback": "http://127.0.0.1:8782/callback?" + callback_id}

    s = requests.session()
    challengee_addr = endpoint + "/.identity/challenge"

    print("")
    pool = Pool(processes=2)
    MyHttpHandler.pubkey = pubkey
    MyHttpHandler.challenge = challenge
    MyHttpHandler.callback_id = callback_id
    server = HTTPServer(('', 8782), MyHttpHandler)

    # start local async callback to receive challengee's response
    p = pool.Process(target=callback_http, args=(server,))
    p.start()

    # send challenge to challengee's well-known object
    s.post(challengee_addr,data=json.dumps(challenge_data))

except Exception as ex:
    sys.exit("Problems retrieving / validating / working with challengee's DID: %s" % str(ex))

time.sleep(3)
p.terminate()
