CREATE DATABASE IF NOT EXISTS blitz_store;
CREATE USER IF NOT EXISTS 'blitzlab'@'localhost' IDENTIFIED BY 'BlitzLab_DB_Only_Local_2026';
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER, INDEX ON blitz_store.* TO 'blitzlab'@'localhost';
GRANT SHOW DATABASES ON *.* TO 'blitzlab'@'localhost';
FLUSH PRIVILEGES;
