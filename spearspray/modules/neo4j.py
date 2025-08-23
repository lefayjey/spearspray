import logging

from neo4j import GraphDatabase
from neo4j.exceptions import AuthError, ServiceUnavailable, ConfigurationError

from spearspray.utils.constants import GREEN, RED, YELLOW, BOLD, RESET

class Neo4j:
    def __init__(self, username, password, uri):

        self.log = logging.getLogger(__name__)

        self.username = username
        self.password = password
        self.uri = uri
        self.driver = None

    def connect(self):
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.username, self.password))
            self.driver.verify_connectivity()
            self.log.info(f"{GREEN}[+]{RESET} Neo4j connection established successfully.")
            return self.driver
        except AuthError:
            self.log.error(f"{RED}[-]{RESET} Neo4j authentication failed. Check username/password.")
            return None
        except ServiceUnavailable:
            self.log.error(f"{RED}[-]{RESET} Neo4j service unavailable. Check if Neo4j is running and URI is correct.")
            return None
        except ConfigurationError as e:
            self.log.error(f"{RED}[-]{RESET} Neo4j configuration error: {e}")
            return None
        except Exception as e:
            self.log.error(f"{RED}[-]{RESET} Unexpected error connecting to Neo4j: {e}")
            return None

    def mark_as_owned(self, user_owned):
        if not self.driver:
            self.log.error(f"{RED}[-]{RESET} No Neo4j connection available. Call connect() first.")
            return False
            
        try:
            with self.driver.session() as session:
                # First, find the user and check current owned status
                find_query = "MATCH (u:User) WHERE u.samaccountname = $username RETURN u.owned as current_owned"
                find_result = session.run(find_query, username=user_owned)
                find_records = list(find_result)
                
                # If user doesn't exist, return False
                if len(find_records) == 0:
                    return False
                
                # Check current owned status
                current_owned = find_records[0]["current_owned"]
                
                # If already owned, return False (no modification needed)
                if current_owned is True:
                    return False
                
                # User exists and is not owned, so mark as owned
                update_query = "MATCH (u:User) WHERE u.samaccountname = $username SET u.owned = true RETURN u.samaccountname as modified_user"
                update_result = session.run(update_query, username=user_owned)
                update_records = list(update_result)
                
                # Return True if the update was successful
                return len(update_records) > 0
                
        except Exception as e:
            self.log.error(f"{RED}[-]{RESET} Error marking user as owned: {e}")
            return False

    def close(self):
        if self.driver:
            self.driver.close()