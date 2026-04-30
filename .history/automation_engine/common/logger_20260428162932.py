from automation_engine.config import LOG_MODE

def log(msg):
    if LOG_MODE == "DEBUG":
        print(msg)

def clean_log(msg):
    print(msg)