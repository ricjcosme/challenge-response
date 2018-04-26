# Challenge / Response python example for Decentralised Identity Hubs (DID based)
A proposal for a simple challenge / response based on the work currently going on at   https://github.com/WebOfTrustInfo/rebooting-the-web-of-trust-spring2018/blob/master/draft-documents/did_auth_draft.md

## Quick & dirty how-to

You'll need [docker](https://docs.docker.com/install/) and [docker-compose](https://docs.docker.com/compose/install/)

For this example we'll use an existing Dominode DID: did:dom:Exgfmw6A5RLWWeJX2G4czjLJb8yDxM whose [DDO (or DID descriptor object)](https://did-resolver.dominode.com/ddo/did:dom:Exgfmw6A5RLWWeJX2G4czjLJb8yDxM) is:
```
{
	"@context": ["https://w3id.org/did/v1"],
	"id": "did:dom:Exgfmw6A5RLWWeJX2G4czjLJb8yDxM",
	"service": [{
		"type": "DidAuthService",
		"serviceEndpoint": "http://127.0.0.1:8781"
	}],
	"authentication": [{
		"type": "Ed25519SignatureAuthentication2018",
		"publicKey": "did:dom:Exgfmw6A5RLWWeJX2G4czjLJb8yDxM#key-1"
	}],
	"publicKey": [{
		"id": "did:dom:Exgfmw6A5RLWWeJX2G4czjLJb8yDxM#key-1",
		"type": "Ed25519VerificationKey2018",
		"owner": "did:dom:Exgfmw6A5RLWWeJX2G4czjLJb8yDxM",
		"publicKeyBase58": "3ofzDb2umnCy96yLwTHawjTCfPZNxPiaX3g9SjN9CwGV"
	}]
}
```


Let's do it then. Open up a terminal window and start typing:
```
git clone https://github.com/ricjcosme/challenge-response.git
cd challenge-response
docker-compose up
```
At this point a DidAuthService docker container is up and running at http://127.0.0.1:8781 - the **"challengee"** or the mentioned DID owner DidAuthService's endpoint listening and waiting for a challenge.

Open up a new terminal window and type:
```
docker run --rm --name challenger --net=host didauthservice python /usr/src/app/challenger.py did:dom:Exgfmw6A5RLWWeJX2G4czjLJb8yDxM
```

The result after a few seconds should be something like:
```
Got challengee DID: did:dom:Exgfmw6A5RLWWeJX2G4czjLJb8yDxM
Generated challenge content: OBWPDPP7S4PKI0S5MSS5P9CGPTDGRI7L
Challengee's DidAuthService endpoint: http://127.0.0.1:8781
Challengee's PublicKey: 3ofzDb2umnCy96yLwTHawjTCfPZNxPiaX3g9SjN9CwGV

Challengee's DID did:dom:Exgfmw6A5RLWWeJX2G4czjLJb8yDxM is legit!!
```

So, what just happened? Simple:
- We've requested the did:dom:Exgfmw6A5RLWWeJX2G4czjLJb8yDxM DDO from the [Universal Resolver](https://github.com/decentralized-identity/universal-resolver)
- We've generated a random challenge (OBWPDPP7S4PKI0S5MSS5P9CGPTDGRI7L)
- We - the **"challenger"** - sent a request to a well-known URI that MUST exist on the designated DidAuthService endpoint (i.e.: http://127.0.0.1:8781/.identity/challenge)
  - Besides the challenge payload, this request also indicated an optional callback endpoint for async response ability - here's the request:
  ```
    {"payload": "OBWPDPP7S4PKI0S5MSS5P9CGPTDGRI7L",
      "callback": "http://127.0.0.1:8782/callback"}
  ```
- The DidAuthService (challengee) replied to the previous request with a HTTP 202.
- Then the DidAuthService (challengee) generated an Ed25519 signature of the challenge it just received
- The DidAuthService (challengee) posted the resulting signature to the challenger's callback - here's the request (which because of its async nature is actually the response in challenge/response):
```
{"payload": "957011e7fe3befdf45ac896954aca21e7e63b1ba29c1f9b34868c0273f3d6f9d840be865ffbc76830d288dc1b33daff3061798e426a375d73928158f28431c07"}
```
- The challenger's callback endpoint will now verify if the signature is valid or not authenticating, this way, the DID
