# codepromptu

Codepromptu is a prompt repository for storing prompts for your LLM applications.

It is a FASTAPI application, backed by a MySQL database.

# installation

Download the GitHub repository: git clone https://github.com/nowucca/codepromptu.git

After that, Install MySQL on your system. (https://dev.mysql.com/downloads/installer/, or brew install mysql on Mac)

Create a codepromptu database, create a user codepromptu with a password that can access the database. 
To do that, you’ll need your root password for mysql (defined during install or is empty). Log in as root and then do:

```sql
DROP SCHEMA IF EXISTS `codepromptu`;
CREATE SCHEMA IF NOT EXISTS `codepromptu`
    DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'codepromptu'@'%' IDENTIFIED BY 'codepromptu_password';
GRANT ALL PRIVILEGES ON codepromptu.* to 'codepromptu'@'%';
FLUSH PRIVILEGES;
```

Run data/scripts/schema.mysql to create the database tables.

You will have to create a .env file (that is not included since it has secrets):

```
DB_HOST=localhost
DB_PORT=3306 (standard port) 
DB_USER=codepromptu (the user you defined)
DB_PASSWORD=codepromptu (the password you chose)
DB_NAME=codepromptu (or the name you chose)
```

Then `python -mvenv venv`, `source venv/bin/activate` and `pip install -r requirements.txt`.

To runt he server, run the FastAPI uvicorn web server:
```
python -m uvicorn main:app --reload
```
