# SpearSpray

Enhance your **Active Directory** password spraying by leveraging user information from Neo4j. 

**SpearSpray** connects to a Neo4j database, retrieves user data (like `samaccountname`, `name`, and `pwdlastset`), and uses that data together with custom patterns defined in `patterns.txt` to generate password wordlists.

## Table of Contents

1. [Features](#features)   
2. [Installation](#installation)  
3. [Usage](#usage)  
4. [TODO](#todo)

## Features

- **Neo4j Connection**: Connects to a Neo4j database to retrieve enabled user information (By default, it removes users whose names contain MSOL or ADSYNC) and generates a `users.txt` file with the `samaccountname` of the users.
- **Password Generation**: Generates password lists based on patterns defined in a text file.
  - **Auto-Generated Wordlists**: Build password candidates for each user using patterns that reference variables such as:
    - `{name}`, `{samaccountname}`, `{year}`, `{short_year}`, `{month_number}`, `{month_en}`, `{season_en}`, etc.
      - You can create new variables by editing the `createLocalVars` function.
  - **Extensible**: Pass additional words via `--extra`, which get inserted into any pattern containing the `{extra}` variable. Additionally, separators and suffixes can be specified via `--separator` and `--suffix`.
  - **No Unnecessary Files**: If a pattern uses `{extra}` but none are provided (`--extra` is empty), that pattern is skipped.
    - Additionally, if a pattern includes the `{separator}` or `{suffix}` variable and they are not defined when calling the script, they will simply be treated as empty strings.
  - **Customizable Patterns**: Define your own placeholders in `patterns.txt` to tailor your spraying strategy.
- **Multi-language Support**: Supports month and season names in both English and Spanish.
- **Ordered Output**: Each generated pattern file aligns user-by-user with the `users.txt` reference file in the output folder.
- **Export**: Saves generated password lists into text files within a specified output folder.

## Installation

1. **Clone** this repository:
   ```bash
   git clone https://github.com/YourUsername/SpearSpray.git
   cd SpearSpray
   ```
2. **Install** Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. **Ensure** you have a running Neo4j instance and valid credentials.

## Usage

1. **Edit** your `patterns.txt` if you want custom password patterns or placeholders. The default patterns are as follows:
   ```bash
   # User as pass
   {samaccountname}

   # Name + Year of the password change
   {name}{separator}{year}{suffix}
   # Name + Year of the password change in short format
   {name}{separator}{short_year}{suffix}
   # Name + Number of the month of the password change + Year of the password change in short format
   {name}{separator}{month_number}{short_year}{suffix}

   # Month of the password change + Year of the password change
   {month_en}{separator}{year}{suffix}
   # Month of the password change + Year of the password change in short format
   {month_en}{separator}{short_year}{suffix}

   # Season of the password change + Year of the password change
   {season_en}{separator}{year}{suffix}
   # Season of the password change + Year of the password change in short format
   {season_en}{separator}{short_year}{suffix}

   # Extra + Year of the password change
   {extra}{separator}{year}{suffix}
   # Extra + Year of the password change in short format
   {extra}{separator}{short_year}{suffix}
   ```
3. **Run** spearspray.py with the desired arguments:
   ```bash
   python spearspray.py -u <NEO4J_USERNAME> -p <NEO4J_PASSWORD> [options]
   ```
   - Available options:
     - `-u`, `--username`: (Required) Neo4j username.
     - `-p`, `--password`: (Required) Neo4j password.
     - `-r`, `--uri`: Neo4j URI (default: neo4j://localhost:7687).
     - `-x`, `--extra`: Comma-separated words to be inserted into `{extra}` placeholders (e.g., "CompanyName,BranchName").
     - `--separator`: String to replace `{separator}` in patterns (default: none).
     - `--suffix`: String to replace `{suffix}` in patterns (default: none).
     - `-i`, `--input`: File containing patterns (default: `patterns.txt`).
     - `-o`, `--output`: Output folder for generated wordlists (default: wordlists).

4. Use the wordlists with your favorite tool and **enjoy spraying!**
   ```
   > python spearspray.py -u neo4j -p neo4j -x Winterfell,Essos --separator '@' --suffix '!'
   
   ╔═╗┌─┐┌─┐┌─┐┬─┐╔═╗┌─┐┬─┐┌─┐┬ ┬
   ╚═╗├─┘├┤ ├─┤├┬┘╚═╗├─┘├┬┘├─┤└┬┘
   ╚═╝┴  └─┘┴ ┴┴└─╚═╝┴  ┴└─┴ ┴ ┴


   [+] Connection established.
   [+] Retrieved 100 users.
   [+] 10 patterns found in patterns.txt.

   [+] Generated pattern #1: samaccountname.txt.
   [+] Generated pattern #2: name_year.txt.
   [+] Generated pattern #3: name_short-year.txt.
   [+] Generated pattern #4: name_month-number_short-year.txt.
   [+] Generated pattern #5: month-en_year.txt.
   [+] Generated pattern #6: month-en_short-year.txt.
   [+] Generated pattern #7: season-en_year.txt.
   [+] Generated pattern #8: season-en_short-year.txt.
   [+] Generated pattern #9: Winterfell_year.txt.
   [+] Generated pattern #9: Essos_year.txt.
   [+] Generated pattern #10: Winterfell_short-year.txt.
   [+] Generated pattern #10: Essos_short-year.txt.

   [+] Wordlists saved to 'wordlists' folder.
   [+] Finish!

   > head wordlists/*
   
   ==> wordlists/users.txt <==
   robb.stark
   daenerys.targaryen

   ==> wordlists/samaccountname.txt <==
   robb.stark
   daenerys.targaryen

   ==> wordlists/Winterfell_short-year.txt <==
   Winterfell@25!
   Winterfell@21!

   ==> wordlists/Winterfell_year.txt <==
   Winterfell@2025!
   Winterfell@2021!

   ==> wordlists/Essos_short-year.txt <==
   Essos@25!
   Essos@21!

   ==> wordlists/Essos_year.txt <==
   Essos@2025!
   Essos@2021!

   ==> wordlists/month-en_short-year.txt <==
   January@25!
   November@21!

   ==> wordlists/month-en_year.txt <==
   January@2025!
   November@2021!

   ==> wordlists/name_month-number_short-year.txt <==
   Robb@0125!
   Daenerys@1121!

   ==> wordlists/name_short-year.txt <==
   Robb@25!
   Daenerys@21!

   ==> wordlists/name_year.txt <==
   Robb@2025!
   Daenerys@2021!

   ==> wordlists/season-en_short-year.txt <==
   Winter@25!
   Autumn@21!

   ==> wordlists/season-en_year.txt <==
   Winter@2025!
   Autumn@2021!

   ```

# TODO

- **Add support for retrieving users via LDAP**.
- **Implement LDAP filters** to allow extracting and generating wordlists only for specific users of interest.
- **Integrate built-in password spraying functionality**, leveraging the `badPwdCount` attribute and the domain’s password policy to optimize attack attempts.
   
