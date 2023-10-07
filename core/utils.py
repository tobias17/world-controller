import re

from core.logger import error

def file_to_class_name(name: str) -> str:
    return name.replace("_", " ").title().replace(" ", "")

def check_name(name: str) -> bool:
    if not name:
        error("filename can not be empty or whitespace")
        return False
    if not re.match("^[a-zA-Z0-9_]+$", name):
        error("filename must only contain the folling characters: [a-zA-Z0-9_]")
        return False
    if not name[0].isalpha():
        error("filename must start with a letter")
        return False
    return True
