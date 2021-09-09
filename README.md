# WireGuard Simple Key Exchange

WireGuard Simple Key Exchange is a tool consisting of two parts: a frontend (api) and a backend (worker). The frontend is where the client can push (register) its key before connecting. The backend (worker) is injecting those keys into a WireGuard instance.
This tool is intended to facilitate running BATMAN over VXLAN over WireGuard as a means to create encrypted high-performance mesh links.

## Installation

### Using pip

This tool can be installed using `pip` (optionally, but suggested inside a venv) after the source has been unpacked/cloned:
```
pip install .
```

### Using Debian packaging / dh-virtualenv

This tool can be packaged for Debian using dh-virtualenv:
```
apt install build-essential debhelper devscripts dh-virtualenv python3-venv
sed "s/#VERSION/$(git describe --tags)/g;s/#DATE/$(date -R)/g" debian/changelog.template > debian/changelog
dpkg-buildpackage -us -uc -b
```

It can then be installed using dpkg:
```
dpkg -i ../wgskex-*.deb
```

The Debian package will automatically create a system user called wgskex and install matching systemd service files.

## Configuration

There are no configuration options (yet)

## Running the worker

* The worker can either be run as root directly using the `worker` script inside `venv/bin` (not suggested) or as normal user with `CAP_NET_ADMIN` capabilities
* An example systemd service file leveraging capabilities can be found inside the debian subfolder

## Running the frontend

* For testing purposes the frontend can be run directly with uvicorn: `uvicron wgskex.frontend:app`
* For prouction usage it is suggested to use gunicorn behind nginx
* An example systemd service file can be found inside the debian subfolder

## Client usage

```
$ wget -q -O- --post-data='{"domain": "ffrgb_tst", "public_key": "o52Ge+Rpj4CUSitVag9mS7pSXUesNM0ESnvj/wwehkg="}'   --header='Content-Type:application/json' 'http://127.0.0.1:8000/api/v1/wg/key/exchange'
{
  "Message": "OK"
}
```
