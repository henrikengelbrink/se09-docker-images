cut -c 1-40 raw.txt > pw_only.txt

# 1. Download password file from HaveIBeenPwnded / Unzip it

# 2. Split passwords from occurrences in file 

`cut -c 1-40 raw.txt > pw_only.txt`

# 3. Count passwords in file

`wc -l pw_only.txt`

# 4. Set password count into code

- load.go (line 12)
- main.go (line 16)
