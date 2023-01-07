# [PyRecruit](https://cjk5642.github.io/PyRecruit/)
An API to collect information on college football and basketball recruits.

This is a Python wrapper API for football recruiting from [247sports](https://247sports.com). 

## Example
```python
from pyrecruit.ncaaf.player import Players
person = Players(year = 2022)

# write as a dataframe
person.dataframe
```
