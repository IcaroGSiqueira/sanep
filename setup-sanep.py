import subprocess

# Check dependencies
print("Checking dependencies...")
try:
    subprocess.check_call(["python3", "setup/dependencies-check.py"])
except subprocess.CalledProcessError as e:
    print("Dependency check failed. Aborting.")
    print(e)
    exit(1)

# Migrate database
print("Running migrations...")
try:
    subprocess.check_call(["python3", "setup/migrate.py"])
except subprocess.CalledProcessError as e:
    print("Migration failed. Aborting.")
    print(e)
    exit(1)

# Seed data
print("Seeding data...")
try:
    subprocess.check_call(["python3", "setup/seed.py"])
except subprocess.CalledProcessError as e:
    print("Data seeding failed. Aborting.")
    print(e)
    exit(1)

print("All scripts executed successfully.")
