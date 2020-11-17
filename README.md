# WireGuard Simple Key Exchange

WireGuard Simple Key Exchange is a tool consisting of two parts: a frontend (api) and a backend (worker). The frontend is where the client can push (register) its key before connecting. The backend (worker) is injecting those keys into a WireGuard instance.
This tool is intended to facilitate running BATMAN over VXLAN over WireGuard as a means to create encrypted high-performance mesh links.

## Installation

* TBA

## Configuration

* TBA

## Running the frontend

* For testing purposes the frontend can be run directly with uvicorn: `uvicron wgskex.frontend:app`
* For prouction usage it is suggested to use gunicorn behind nginx

## Client usage

```
$ wget -q -O- --post-data='{"domain": "ffrgb_tst", "public_key": "o52Ge+Rpj4CUSitVag9mS7pSXUesNM0ESnvj/wwehkg="}'   --header='Content-Type:application/json' 'http://127.0.0.1:8000/api/v1/wg/key/exchange'
{
  "Message": "OK"
}
```
