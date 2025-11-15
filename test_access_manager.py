"""
Test script for Snowflake Access Manager

This script tests the AccessManager functionality including:
- Connection to Snowflake
- Role creation
- Permission grants
- User management
- Quick setup functions

Run this script to verify the access manager is working correctly.
"""

import sys
from snowflake_access_manager import AccessManager, quick_setup_readonly, quick_setup_analyst


def test_connection():
    """Test basic connection to Snowflake."""
    print("\n" + "=" * 80)
    print("TEST 1: Connection Test")
    print("=" * 80)

    try:
        manager = AccessManager()
        manager.connect()

        # Test a simple query
        result = manager.execute_query("SELECT CURRENT_USER(), CURRENT_ROLE(), CURRENT_DATABASE()")
        print(f"\n✓ Connected successfully!")
        print(f"  User: {result[0][0]}")
        print(f"  Role: {result[0][1]}")
        print(f"  Database: {result[0][2]}")

        manager.disconnect()
        return True
    except Exception as e:
        print(f"\n✗ Connection test failed: {e}")
        return False


def test_role_creation():
    """Test creating a role."""
    print("\n" + "=" * 80)
    print("TEST 2: Role Creation")
    print("=" * 80)

    try:
        manager = AccessManager()
        manager.connect()

        # Create a test role
        test_role = "TEST_ROLE_TEMP"
        success = manager.create_role(test_role, "Temporary test role")

        if success:
            print(f"\n✓ Role creation test passed")

            # Clean up - drop the test role
            try:
                manager.execute_query(f"DROP ROLE IF EXISTS {test_role}")
                print(f"✓ Cleaned up test role")
            except:
                pass

        manager.disconnect()
        return success
    except Exception as e:
        print(f"\n✗ Role creation test failed: {e}")
        return False


def test_warehouse_access():
    """Test granting warehouse access."""
    print("\n" + "=" * 80)
    print("TEST 3: Warehouse Access Grant")
    print("=" * 80)

    try:
        manager = AccessManager()
        manager.connect()

        # Create a test role
        test_role = "TEST_WAREHOUSE_ROLE"
        manager.create_role(test_role, "Test role for warehouse access")

        # Grant warehouse access
        success = manager.grant_warehouse_access(manager.warehouse, test_role)

        if success:
            print(f"\n✓ Warehouse access grant test passed")

            # Show grants
            manager.show_grants_for_role(test_role)

            # Clean up
            try:
                manager.execute_query(f"DROP ROLE IF EXISTS {test_role}")
                print(f"✓ Cleaned up test role")
            except:
                pass

        manager.disconnect()
        return success
    except Exception as e:
        print(f"\n✗ Warehouse access test failed: {e}")
        return False


def test_database_and_schema_access():
    """Test granting database and schema access."""
    print("\n" + "=" * 80)
    print("TEST 4: Database and Schema Access Grant")
    print("=" * 80)

    try:
        manager = AccessManager()
        manager.connect()

        # Create a test role
        test_role = "TEST_DB_SCHEMA_ROLE"
        manager.create_role(test_role, "Test role for database/schema access")

        # Grant database access
        db_success = manager.grant_database_access(manager.database, test_role)

        # Grant schema access
        schema_success = manager.grant_schema_access(manager.database, manager.schema, test_role)

        success = db_success and schema_success

        if success:
            print(f"\n✓ Database and schema access grant test passed")

            # Show grants
            manager.show_grants_for_role(test_role)

            # Clean up
            try:
                manager.execute_query(f"DROP ROLE IF EXISTS {test_role}")
                print(f"✓ Cleaned up test role")
            except:
                pass

        manager.disconnect()
        return success
    except Exception as e:
        print(f"\n✗ Database/schema access test failed: {e}")
        return False


def test_table_access():
    """Test granting table access."""
    print("\n" + "=" * 80)
    print("TEST 5: Table Access Grant")
    print("=" * 80)

    try:
        manager = AccessManager()
        manager.connect()

        # Create a test role
        test_role = "TEST_TABLE_ROLE"
        manager.create_role(test_role, "Test role for table access")

        # Grant access to all tables
        success = manager.grant_table_access(
            manager.database,
            manager.schema,
            '*',
            test_role,
            ['SELECT']
        )

        # Grant future table access
        future_success = manager.grant_future_table_access(
            manager.database,
            manager.schema,
            test_role,
            ['SELECT']
        )

        success = success and future_success

        if success:
            print(f"\n✓ Table access grant test passed")

            # Show grants
            manager.show_grants_for_role(test_role)

            # Clean up
            try:
                manager.execute_query(f"DROP ROLE IF EXISTS {test_role}")
                print(f"✓ Cleaned up test role")
            except:
                pass

        manager.disconnect()
        return success
    except Exception as e:
        print(f"\n✗ Table access test failed: {e}")
        return False


def test_read_only_setup():
    """Test the read-only access setup."""
    print("\n" + "=" * 80)
    print("TEST 6: Read-Only Access Setup")
    print("=" * 80)

    try:
        manager = AccessManager()
        manager.connect()

        # Setup read-only access
        test_role = "TEST_READONLY_ROLE"
        success = manager.setup_read_only_access(role_name=test_role)

        if success:
            print(f"\n✓ Read-only setup test passed")

            # Show what was granted
            manager.show_grants_for_role(test_role)

            # Clean up
            try:
                manager.execute_query(f"DROP ROLE IF EXISTS {test_role}")
                print(f"✓ Cleaned up test role")
            except:
                pass

        manager.disconnect()
        return success
    except Exception as e:
        print(f"\n✗ Read-only setup test failed: {e}")
        return False


def test_analyst_setup():
    """Test the data analyst access setup."""
    print("\n" + "=" * 80)
    print("TEST 7: Data Analyst Access Setup")
    print("=" * 80)

    try:
        manager = AccessManager()
        manager.connect()

        # Setup analyst access
        test_role = "TEST_ANALYST_ROLE"
        success = manager.setup_data_analyst_access(role_name=test_role)

        if success:
            print(f"\n✓ Data analyst setup test passed")

            # Show what was granted
            manager.show_grants_for_role(test_role)

            # Clean up
            try:
                manager.execute_query(f"DROP ROLE IF EXISTS {test_role}")
                print(f"✓ Cleaned up test role")
            except:
                pass

        manager.disconnect()
        return success
    except Exception as e:
        print(f"\n✗ Data analyst setup test failed: {e}")
        return False


def run_all_tests():
    """Run all tests and report results."""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "SNOWFLAKE ACCESS MANAGER TEST SUITE" + " " * 23 + "║")
    print("╚" + "=" * 78 + "╝")

    tests = [
        ("Connection Test", test_connection),
        ("Role Creation", test_role_creation),
        ("Warehouse Access Grant", test_warehouse_access),
        ("Database & Schema Access Grant", test_database_and_schema_access),
        ("Table Access Grant", test_table_access),
        ("Read-Only Setup", test_read_only_setup),
        ("Data Analyst Setup", test_analyst_setup),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ Test '{test_name}' crashed: {e}")
            results.append((test_name, False))

    # Print summary
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 30 + "TEST SUMMARY" + " " * 36 + "║")
    print("╚" + "=" * 78 + "╝")
    print()

    passed = 0
    failed = 0

    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        status_color = "\033[92m" if result else "\033[91m"
        reset_color = "\033[0m"

        print(f"  {status_color}{status}{reset_color}  {test_name}")

        if result:
            passed += 1
        else:
            failed += 1

    print()
    print("=" * 80)
    print(f"Total: {len(results)} tests  |  Passed: {passed}  |  Failed: {failed}")
    print("=" * 80)

    if failed == 0:
        print("\n🎉 All tests passed! The Access Manager is working correctly.")
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please check the errors above.")

    print()

    return failed == 0


if __name__ == "__main__":
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n✗ Fatal error during testing: {e}")
        sys.exit(1)
