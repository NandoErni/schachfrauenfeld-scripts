# Chess Club Event Parser

Converts a plain text chess club schedule into a WordPress-compatible CSV import file.

## Usage

```bash
python parse_events.py
```

input file ise `events.txt` and output file is `events.csv`

configure slugs and default location using constants in python code:

```python
DEFAULT_LOCATION = "Klublokal"

CATEGORY_KLUBABEND = ""
CATEGORY_FERIEN = ""
CATEGORY_SGM = "SGM/SMM"
CATEGORY_SMM = "SGM/SMM"
CATEGORY_KLUBMEISTERSCHAFT = "Klubmeisterschaft"
CATEGORY_STADTMEISTERSCHAFT = "Stadtmeisterschaft"
```
