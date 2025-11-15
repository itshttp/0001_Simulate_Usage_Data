"""
Snowflake Access Manager

This module provides automated access management for Snowflake resources.
It uses admin credentials from .env to grant necessary permissions to users,
roles, warehouses, databases, schemas, and tables.

Features:
- Automatic permission granting using admin credentials
- Role creation and management
- User access management
- Warehouse, database, schema, and table permissions
- Batch permission operations

Setup:
1. Ensure .env file contains admin credentials (with ACCOUNTADMIN role)
2. Import and use the functions to grant access as needed

Example:
    from snowflake_access_manager import AccessManager

    # Initialize with admin credentials from .env
    manager = AccessManager()

    # Grant permissions
    manager.grant_warehouse_access('MY_WAREHOUSE', 'DATA_ANALYST_ROLE')
    manager.grant_database_access('MY_DATABASE', 'DATA_ANALYST_ROLE')
    manager.grant_schema_access('MY_DATABASE', 'PUBLIC', 'DATA_ANALYST_ROLE')
"""

import os
import snowflake.connector
from dotenv import load_dotenv
from typing import List, Optional, Dict, Any
from datetime import datetime

# Load environment variables
load_dotenv()


class AccessManager:
    """
    Manages Snowflake access control and permissions using admin credentials.
    """

    def __init__(self):
        """Initialize the AccessManager with admin credentials from .env"""
        self.conn = None
        self.cursor = None
        self._load_admin_credentials()

    def _load_admin_credentials(self):
        """Load and validate admin credentials from environment variables."""
        required_vars = [
            'SNOWFLAKE_ACCOUNT',
            'SNOWFLAKE_USER',
            'SNOWFLAKE_PASSWORD',
            'SNOWFLAKE_WAREHOUSE',
            'SNOWFLAKE_DATABASE',
            'SNOWFLAKE_SCHEMA'
        ]

        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing_vars)}\n"
                f"Please ensure your .env file contains admin credentials."
            )

        self.account = os.getenv('SNOWFLAKE_ACCOUNT')
        self.user = os.getenv('SNOWFLAKE_USER')
        self.password = os.getenv('SNOWFLAKE_PASSWORD')
        self.warehouse = os.getenv('SNOWFLAKE_WAREHOUSE')
        self.database = os.getenv('SNOWFLAKE_DATABASE')
        self.schema = os.getenv('SNOWFLAKE_SCHEMA')
        self.role = os.getenv('SNOWFLAKE_ROLE', 'ACCOUNTADMIN')

        print(f"✓ Admin credentials loaded for user: {self.user}")
        print(f"✓ Using role: {self.role}")

    def connect(self):
        """Establish connection to Snowflake using admin credentials."""
        try:
            self.conn = snowflake.connector.connect(
                account=self.account,
                user=self.user,
                password=self.password,
                warehouse=self.warehouse,
                database=self.database,
                schema=self.schema,
                role=self.role
            )
            self.cursor = self.conn.cursor()
            print(f"✓ Connected to Snowflake as {self.user} with {self.role} role")
            return True
        except Exception as e:
            print(f"✗ Failed to connect to Snowflake: {e}")
            raise

    def disconnect(self):
        """Close the Snowflake connection."""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
            print("✓ Disconnected from Snowflake")

    def execute_query(self, query: str, params: Optional[tuple] = None) -> Any:
        """
        Execute a SQL query and return results.

        Args:
            query: SQL query to execute
            params: Optional query parameters

        Returns:
            Query results
        """
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            return self.cursor.fetchall()
        except Exception as e:
            print(f"✗ Query execution failed: {e}")
            print(f"  Query: {query}")
            raise

    def create_role(self, role_name: str, comment: str = None) -> bool:
        """
        Create a new role in Snowflake.

        Args:
            role_name: Name of the role to create
            comment: Optional comment describing the role

        Returns:
            True if successful, False otherwise
        """
        try:
            query = f"CREATE ROLE IF NOT EXISTS {role_name}"
            if comment:
                query += f" COMMENT = '{comment}'"

            self.execute_query(query)
            print(f"✓ Role '{role_name}' created/verified")
            return True
        except Exception as e:
            print(f"✗ Failed to create role '{role_name}': {e}")
            return False

    def grant_role_to_user(self, role_name: str, user_name: str) -> bool:
        """
        Grant a role to a user.

        Args:
            role_name: Role to grant
            user_name: User to grant the role to

        Returns:
            True if successful, False otherwise
        """
        try:
            query = f"GRANT ROLE {role_name} TO USER {user_name}"
            self.execute_query(query)
            print(f"✓ Granted role '{role_name}' to user '{user_name}'")
            return True
        except Exception as e:
            print(f"✗ Failed to grant role '{role_name}' to user '{user_name}': {e}")
            return False

    def grant_warehouse_access(self, warehouse_name: str, role_name: str,
                               privileges: List[str] = None) -> bool:
        """
        Grant warehouse access to a role.

        Args:
            warehouse_name: Name of the warehouse
            role_name: Role to grant access to
            privileges: List of privileges (default: ['USAGE'])

        Returns:
            True if successful, False otherwise
        """
        if privileges is None:
            privileges = ['USAGE']

        try:
            for privilege in privileges:
                query = f"GRANT {privilege} ON WAREHOUSE {warehouse_name} TO ROLE {role_name}"
                self.execute_query(query)
                print(f"✓ Granted {privilege} on warehouse '{warehouse_name}' to role '{role_name}'")
            return True
        except Exception as e:
            print(f"✗ Failed to grant warehouse access: {e}")
            return False

    def grant_database_access(self, database_name: str, role_name: str,
                             privileges: List[str] = None) -> bool:
        """
        Grant database access to a role.

        Args:
            database_name: Name of the database
            role_name: Role to grant access to
            privileges: List of privileges (default: ['USAGE'])

        Returns:
            True if successful, False otherwise
        """
        if privileges is None:
            privileges = ['USAGE']

        try:
            for privilege in privileges:
                query = f"GRANT {privilege} ON DATABASE {database_name} TO ROLE {role_name}"
                self.execute_query(query)
                print(f"✓ Granted {privilege} on database '{database_name}' to role '{role_name}'")
            return True
        except Exception as e:
            print(f"✗ Failed to grant database access: {e}")
            return False

    def grant_schema_access(self, database_name: str, schema_name: str,
                           role_name: str, privileges: List[str] = None) -> bool:
        """
        Grant schema access to a role.

        Args:
            database_name: Name of the database
            schema_name: Name of the schema
            role_name: Role to grant access to
            privileges: List of privileges (default: ['USAGE'])

        Returns:
            True if successful, False otherwise
        """
        if privileges is None:
            privileges = ['USAGE']

        try:
            for privilege in privileges:
                query = f"GRANT {privilege} ON SCHEMA {database_name}.{schema_name} TO ROLE {role_name}"
                self.execute_query(query)
                print(f"✓ Granted {privilege} on schema '{database_name}.{schema_name}' to role '{role_name}'")
            return True
        except Exception as e:
            print(f"✗ Failed to grant schema access: {e}")
            return False

    def grant_table_access(self, database_name: str, schema_name: str,
                          table_name: str, role_name: str,
                          privileges: List[str] = None) -> bool:
        """
        Grant table access to a role.

        Args:
            database_name: Name of the database
            schema_name: Name of the schema
            table_name: Name of the table (use '*' for all tables)
            role_name: Role to grant access to
            privileges: List of privileges (default: ['SELECT'])

        Returns:
            True if successful, False otherwise
        """
        if privileges is None:
            privileges = ['SELECT']

        try:
            for privilege in privileges:
                if table_name == '*':
                    query = f"GRANT {privilege} ON ALL TABLES IN SCHEMA {database_name}.{schema_name} TO ROLE {role_name}"
                else:
                    query = f"GRANT {privilege} ON TABLE {database_name}.{schema_name}.{table_name} TO ROLE {role_name}"
                self.execute_query(query)
                print(f"✓ Granted {privilege} on table '{database_name}.{schema_name}.{table_name}' to role '{role_name}'")
            return True
        except Exception as e:
            print(f"✗ Failed to grant table access: {e}")
            return False

    def grant_future_table_access(self, database_name: str, schema_name: str,
                                  role_name: str, privileges: List[str] = None) -> bool:
        """
        Grant access to future tables in a schema.

        Args:
            database_name: Name of the database
            schema_name: Name of the schema
            role_name: Role to grant access to
            privileges: List of privileges (default: ['SELECT'])

        Returns:
            True if successful, False otherwise
        """
        if privileges is None:
            privileges = ['SELECT']

        try:
            for privilege in privileges:
                query = f"GRANT {privilege} ON FUTURE TABLES IN SCHEMA {database_name}.{schema_name} TO ROLE {role_name}"
                self.execute_query(query)
                print(f"✓ Granted {privilege} on future tables in '{database_name}.{schema_name}' to role '{role_name}'")
            return True
        except Exception as e:
            print(f"✗ Failed to grant future table access: {e}")
            return False

    def create_user(self, user_name: str, password: str, email: str = None,
                   default_role: str = None, default_warehouse: str = None) -> bool:
        """
        Create a new user in Snowflake.

        Args:
            user_name: Username for the new user
            password: Password for the new user
            email: Optional email address
            default_role: Optional default role
            default_warehouse: Optional default warehouse

        Returns:
            True if successful, False otherwise
        """
        try:
            query = f"CREATE USER IF NOT EXISTS {user_name} PASSWORD = '{password}'"

            if email:
                query += f" EMAIL = '{email}'"
            if default_role:
                query += f" DEFAULT_ROLE = {default_role}"
            if default_warehouse:
                query += f" DEFAULT_WAREHOUSE = {default_warehouse}"

            self.execute_query(query)
            print(f"✓ User '{user_name}' created/verified")
            return True
        except Exception as e:
            print(f"✗ Failed to create user '{user_name}': {e}")
            return False

    def setup_read_only_access(self, role_name: str = "READ_ONLY_ROLE",
                               user_name: str = None) -> bool:
        """
        Setup a read-only role with access to current database and schema.

        Args:
            role_name: Name of the read-only role to create
            user_name: Optional user to grant this role to

        Returns:
            True if successful, False otherwise
        """
        try:
            print(f"\nSetting up read-only access...")
            print("-" * 60)

            # Create role
            self.create_role(role_name, "Read-only access to data")

            # Grant warehouse usage
            self.grant_warehouse_access(self.warehouse, role_name)

            # Grant database usage
            self.grant_database_access(self.database, role_name)

            # Grant schema usage
            self.grant_schema_access(self.database, self.schema, role_name)

            # Grant SELECT on all existing tables
            self.grant_table_access(self.database, self.schema, '*', role_name, ['SELECT'])

            # Grant SELECT on future tables
            self.grant_future_table_access(self.database, self.schema, role_name, ['SELECT'])

            # Grant to user if specified
            if user_name:
                self.grant_role_to_user(role_name, user_name)

            print("-" * 60)
            print(f"✓ Read-only access setup complete for role '{role_name}'")
            return True

        except Exception as e:
            print(f"✗ Failed to setup read-only access: {e}")
            return False

    def setup_data_analyst_access(self, role_name: str = "DATA_ANALYST_ROLE",
                                  user_name: str = None) -> bool:
        """
        Setup a data analyst role with read/write access to current database.

        Args:
            role_name: Name of the data analyst role to create
            user_name: Optional user to grant this role to

        Returns:
            True if successful, False otherwise
        """
        try:
            print(f"\nSetting up data analyst access...")
            print("-" * 60)

            # Create role
            self.create_role(role_name, "Data analyst with read/write access")

            # Grant warehouse usage
            self.grant_warehouse_access(self.warehouse, role_name, ['USAGE', 'OPERATE'])

            # Grant database usage and create schema
            self.grant_database_access(self.database, role_name, ['USAGE', 'CREATE SCHEMA'])

            # Grant schema all privileges
            self.grant_schema_access(self.database, self.schema, role_name,
                                    ['USAGE', 'CREATE TABLE', 'CREATE VIEW'])

            # Grant SELECT, INSERT, UPDATE, DELETE on all existing tables
            self.grant_table_access(self.database, self.schema, '*', role_name,
                                   ['SELECT', 'INSERT', 'UPDATE', 'DELETE'])

            # Grant privileges on future tables
            self.grant_future_table_access(self.database, self.schema, role_name,
                                          ['SELECT', 'INSERT', 'UPDATE', 'DELETE'])

            # Grant to user if specified
            if user_name:
                self.grant_role_to_user(role_name, user_name)

            print("-" * 60)
            print(f"✓ Data analyst access setup complete for role '{role_name}'")
            return True

        except Exception as e:
            print(f"✗ Failed to setup data analyst access: {e}")
            return False

    def show_grants_for_role(self, role_name: str):
        """
        Display all grants for a specific role.

        Args:
            role_name: Role name to show grants for
        """
        try:
            query = f"SHOW GRANTS TO ROLE {role_name}"
            results = self.execute_query(query)

            print(f"\nGrants for role '{role_name}':")
            print("-" * 80)
            for row in results:
                print(f"  {row}")
            print("-" * 80)

        except Exception as e:
            print(f"✗ Failed to show grants for role '{role_name}': {e}")

    def show_roles_for_user(self, user_name: str):
        """
        Display all roles granted to a user.

        Args:
            user_name: Username to show roles for
        """
        try:
            query = f"SHOW GRANTS TO USER {user_name}"
            results = self.execute_query(query)

            print(f"\nRoles for user '{user_name}':")
            print("-" * 80)
            for row in results:
                print(f"  {row}")
            print("-" * 80)

        except Exception as e:
            print(f"✗ Failed to show roles for user '{user_name}': {e}")


def quick_setup_readonly(user_name: str = None):
    """
    Quick helper function to setup read-only access.

    Args:
        user_name: Optional user to grant read-only access to
    """
    manager = AccessManager()
    try:
        manager.connect()
        manager.setup_read_only_access(user_name=user_name)
    finally:
        manager.disconnect()


def quick_setup_analyst(user_name: str = None):
    """
    Quick helper function to setup data analyst access.

    Args:
        user_name: Optional user to grant analyst access to
    """
    manager = AccessManager()
    try:
        manager.connect()
        manager.setup_data_analyst_access(user_name=user_name)
    finally:
        manager.disconnect()


if __name__ == "__main__":
    # Example usage
    import argparse

    parser = argparse.ArgumentParser(description='Manage Snowflake access and permissions')
    parser.add_argument('--setup-readonly', action='store_true',
                       help='Setup read-only role')
    parser.add_argument('--setup-analyst', action='store_true',
                       help='Setup data analyst role')
    parser.add_argument('--user', type=str,
                       help='User to grant role to')
    parser.add_argument('--show-grants', type=str,
                       help='Show grants for a role')

    args = parser.parse_args()

    if args.setup_readonly:
        quick_setup_readonly(args.user)
    elif args.setup_analyst:
        quick_setup_analyst(args.user)
    elif args.show_grants:
        manager = AccessManager()
        try:
            manager.connect()
            manager.show_grants_for_role(args.show_grants)
        finally:
            manager.disconnect()
    else:
        print("Please specify an action. Use --help for options.")
