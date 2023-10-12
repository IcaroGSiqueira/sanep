import subprocess

# Check dependencies
print("Checking dependencies...")
try:
    subprocess.check_call(['python3', 'dependencies-check.py'])
except subprocess.CalledProcessError as e:
    print("Dependency check failed. Aborting.")
    print(e)
    exit(1)

# Migrate database
print("Running migrations...")
try:
    subprocess.check_call(['python3', 'migrate.py'])
except subprocess.CalledProcessError as e:
    print("Migration failed. Aborting.")
    print(e)
    exit(1)

# Seed data
print("Seeding data...")
try:
    subprocess.check_call(['python3', 'seed.py'])
except subprocess.CalledProcessError as e:
    print("Data seeding failed. Aborting.")
    print(e)
    exit(1)

# Run main script
print("Starting main script...")
try:
    subprocess.check_call(['pm2', 'start', 'pm2.config.js', '--interpreter=python3', '--watch'])
except subprocess.CalledProcessError as e:
    print("Main script execution failed. Aborting.")
    print(e)
    exit(1)

print("All scripts executed successfully.")
