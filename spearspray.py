from neo4j import GraphDatabase
from unidecode import unidecode
import argparse
import sys
import datetime
import os
import re

banner = """
╔═╗┌─┐┌─┐┌─┐┬─┐╔═╗┌─┐┬─┐┌─┐┬ ┬
╚═╗├─┘├┤ ├─┤├┬┘╚═╗├─┘├┬┘├─┤└┬┘
╚═╝┴  └─┘┴ ┴┴└─╚═╝┴  ┴└─┴ ┴ ┴

"""

MONTH_NAMES_ES = {
    1: "Enero",	2: "Febrero", 3: "Marzo", 4: "Abril",
    5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
    9: "Septiembre", 10: "Octubre",	11: "Noviembre", 12: "Diciembre"
}

MONTH_NAMES_EN = {
    1: "January", 2: "February", 3: "March", 4: "April",
    5: "May", 6: "June", 7: "July", 8: "August",
    9: "September", 10: "October", 11: "November", 12: "December"
}

SEASONS_ES = {
    1: "Invierno", 2: "Invierno", 3: "Primavera", 4: "Primavera",
    5: "Primavera", 6: "Verano", 7: "Verano", 8: "Verano",
    9: "Otoño", 10: "Otoño", 11: "Otoño", 12: "Invierno"
}

SEASONS_EN = {
    1: "Winter", 2: "Winter", 3: "Spring", 4: "Spring",
    5: "Spring", 6: "Summer", 7: "Summer", 8: "Summer",
    9: "Autumn", 10: "Autumn", 11: "Autumn", 12: "Winter"
}

# Parse the command-line arguments.

def parseArguments():

    parser = argparse.ArgumentParser(
                        prog='SpearSpray',
                        description='Enhance Your Active Directory Spraying with User Information!',
                        epilog="Example: python spearspray.py -u neo4j -p bloodhound -x CompanyName,BranchName --separator '@' --suffix '!'")

    parser.add_argument('-u', '--username', type=str, metavar='USER', help='Neo4j username (required).', required=True)
    parser.add_argument('-p', '--password', type=str, metavar='PASSWORD', help='Neo4j password (required).', required=True)

    parser.add_argument('-r', '--uri', type=str, metavar='URI', help='Neo4j URI (default: neo4j://localhost:7687)', default='neo4j://localhost:7687', required=False)
    parser.add_argument('-x', '--extra', type=str, metavar='EXTRA WORDS', help='Comma-separated extra words to be used in patterns that utilize the {extra} variable. (e.g. CompanyName,BranchName).', required=False)
    parser.add_argument('--separator', type=str, metavar='SEPARATOR', help='Characters to insert between generated patterns that use the {separator} variable. (default: none).', required=False)
    parser.add_argument('--suffix', type=str, metavar='SUFFIX', help='Characters to append at the end of each generated pattern that uses the {suffix} variable. (default: none).', required=False)
    parser.add_argument('-i', '--input', type=str, metavar='INPUT', help='File with defined patterns (default: patterns.txt).', default='patterns.txt', required=False)
    parser.add_argument('-o', '--output', type=str, metavar='OUTPUT', help='Folder where the generated wordlists will be stored (default: wordlists).', default='wordlists', required=False)

    return parser.parse_args()

# Establish connection to Neo4j database

def connectdb(uri, auth):

    try:
        driver = GraphDatabase.driver(uri, auth=auth)
        driver.verify_connectivity()
        print("[+] Connection established.")
        return driver

    except Exception as e:
        print(f"[-] Error connection.")
        sys.exit(1)

# Retrieve enabled users from Neo4j, excluding those with MSOL/ADSYNC in their samaccountname

def getUsers(driver):

    query = """
    MATCH (u:User)
    WHERE (u.enabled = True OR u.enabled IS NULL)
    AND NOT (
    u.samaccountname =~ "(?i).*msol.*" OR
    u.samaccountname =~ "(?i).*adsync.*"
    )
    RETURN COALESCE (u.displayname, u.samaccountname) AS name,
        u.samaccountname AS samaccountname,
        u.pwdlastset AS pwdlastset"""

    with driver.session() as session:
        records = list(session.run(query))

    users = []
    for r in records:
        users.append({
            "name": r["name"],
            "samaccountname": r["samaccountname"],
            "pwdlastset": r["pwdlastset"]
        })

    print(f"[+] Retrieved {len(users)} users.")

    return users

# Load patterns from the specified file, ignoring comments

def loadPatterns(pattern_file):

    patterns = []
    with open(pattern_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()

            if line and not line.startswith('#'):
                patterns.append(line)

    print(f"[+] {len(patterns)} patterns found in patterns.txt.\n")

    return patterns

# Check if the pattern uses the {extra} placeholder

def patternUsesExtra(pattern):
  
    return "{extra}" in pattern

# Create local variables from user data for pattern substitution

def createLocalVars(user, extra, separator, suffix):

    raw_name = user.get("name")
    name = unidecode(raw_name.split()[0])

    sam = user.get("samaccountname", "")

    dt = datetime.datetime.fromtimestamp(user.get("pwdlastset"))
    pwddate = dt.strftime('%d/%m/%Y')
    month = dt.month

    month_name_es = MONTH_NAMES_ES.get(month)
    month_name_en = MONTH_NAMES_EN.get(month)

    season_es = SEASONS_ES.get(month)
    season_en = SEASONS_EN.get(month)

    return {
        "name": name,
        "samaccountname": sam,
        "year": pwddate[-4:],
        "short_year": pwddate[-2:],
        "month_number": pwddate[3:5],
        "month_es": month_name_es,
        "month_en": month_name_en,
        "season_es": season_es,
        "season_en": season_en,
        "extra": extra or "",
        "separator": separator or "",
        "suffix": suffix or ""
    }

# Generate passwords based on the provided pattern and user data

def buildPasswordsForPattern(pattern, users, extra_word, separator, suffix, i):

    passwords = []
    for user in users:
        # For each user, the variables that the pattern will use are created.
        vars_ = createLocalVars(user, extra_word, separator, suffix)

        try:
            # eval is used with a dynamic f-string to populate
            # the pattern placeholders with the values from vars_.
            pwd = eval(f'f"{pattern}"', {}, vars_)
            passwords.append(pwd)
        except Exception as ex:
            print(f"[-] Error generating pattern #{i}: {ex}")
            return []

    return passwords

# Create wordlists for each pattern and write them to output files

def createWordlists(users, pattern_file, extra, separator, suffix, out_dir):

    # A folder is created to store the generated wordlists.
    os.makedirs(out_dir, exist_ok=True)

    # A user dictionary is created from the users.txt file.
    users_txt_path = os.path.join(out_dir, "users.txt")
    with open(users_txt_path, "w", encoding="utf-8") as uf:
        for usr in users:
            uf.write(usr["samaccountname"] + "\n")

    # Patterns are loaded from the patterns.txt file.
    patterns = loadPatterns(pattern_file)

    # The value(s) of the extra argument are parsed if the argument is provided.
    extra_list = []
    if extra:
        extra_list = [x.strip() for x in extra.split(',') if x.strip()]

    # Each pattern is processed individually.
    for i, pat in enumerate(patterns, start=1):
        
        # A name is generated for each pattern, which will be used as the filename for the corresponding output file.
        pat_name = re.sub(r'\{separator\}|\{suffix\}', '', pat)
        pat_name = re.sub(r'_', '-', pat_name)
        pat_name = re.sub(r'[{}]', '_', pat_name)
        pat_name = re.sub(r'_+', '_', pat_name)
        pat_name = pat_name.strip('_')
        
        if patternUsesExtra(pat):
            # If the pattern uses {extra}, the script checks whether extra values have been provided via the extra argument.
            if not extra_list:
                # If no extra values are provided, no file will be generated for the pattern that uses {extra}.
                print(f"[-] Skipping pattern #{i} (requires '{{extra}}', but no extras were provided).")
                continue
            else:
                # If extra values are provided, a separate file is generated for each extra word.
                for e in extra_list:
                    tmp_pat_name = re.sub(r'extra', e, pat_name)
                    filename = f"{tmp_pat_name}.txt"
                    filepath = os.path.join(out_dir, filename)
                    # The buildPasswordsForPattern function is called with the following parameters:
                    # the pattern, the list of users, a word from the extra values list, the separator, the suffix and finally the pattern number.
                    pwds = buildPasswordsForPattern(pat, users, e, separator, suffix, i)
                    if pwds:
                        with open(filepath, "w", encoding="utf-8") as pf:
                            for p_line in pwds:
                                pf.write(p_line + "\n")
                        print(f"[+] Generated pattern #{i}: {filename}.")

        else:
            # If the pattern does not use {extra}, only one file is generated for that pattern.
            filename = f"{pat_name}.txt"
            filepath = os.path.join(out_dir, filename)

            pwds = buildPasswordsForPattern(pat, users, "", separator, suffix, i)
            if pwds:
                with open(filepath, "w", encoding="utf-8") as pf:
                    for p_line in pwds:
                        pf.write(p_line + "\n")
                print(f"[+] Generated pattern #{i}: {filename}.")

def main():

    print(banner)
    args = parseArguments()

    driver = connectdb(args.uri, (args.username, args.password))
    users = getUsers(driver)
    driver.close()

    createWordlists(users, args.input, args.extra, args.separator, args.suffix, args.output)

    print("\n[+] Wordlists saved to '" + args.output + "' folder.")

    print("[+] Finish!\n")

if __name__ == "__main__":

    main()
