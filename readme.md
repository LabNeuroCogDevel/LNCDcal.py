# LNCDcal
operations on Goolge calendar for LNCD.
Convenience functions on top of `googleapiclient.discovery.build` using `oauth2client.service_account.ServiceAccountCredentials` 

This has to have been implemented better elsewhere

## What
provides:
 * `get_event`
 * `insert_event`
 * `delete_event`
 * `move_event`
 * `upcoming`
 * `find_in_range`

from settings in `cal.ini` specifying
  * a service account (`email` field)
  * path to a `*.p12` key 
  * calendar id where service account has manager permissions (see google calendar settings)
  * Optionally: a different calendar id for `move_event`


## Install
```
pip3 install git+https://github.com/LabNeuroCogDevel/LNCDcal.py
```

## Configure

Configuration in ini style file (via `configparser`). see `cal.ini.example`.

## Usage

```python
import LNCDcal
cal = LNCDcal.LCNDcal('cal.ini')
```

also see `LNCDcal/test_LNCDcal.py`
