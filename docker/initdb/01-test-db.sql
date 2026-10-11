-- Create the test database used by pytest
SELECT 'CREATE DATABASE loomlink_test' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'loomlink_test')\gexec
GRANT ALL PRIVILEGES ON DATABASE loomlink_test TO loomlink;
