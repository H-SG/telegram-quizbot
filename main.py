import tomllib
from pathlib import Path


CONFIG_PATH: Path = Path("./config.toml")
QUIZ_PATH: Path = Path("./quiz.toml")

with open(QUIZ_PATH, 'rb') as qp:
    QUIZ_DICT: dict = tomllib.load(qp)

with open(CONFIG_PATH, 'rb') as cp:
    CONFIG_DICT: dict = tomllib.load(cp)

print('wait')