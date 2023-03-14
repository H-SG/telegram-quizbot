import tomllib
from pathlib import Path

QUIZ_PATH: Path = Path("./quiz.toml")

with open(QUIZ_PATH, "rb") as qp:
    QUIZ_DICT: dict = tomllib.load(qp)

assert 'winner' in QUIZ_DICT.keys()
del QUIZ_DICT['winner']

assert 'failed' in QUIZ_DICT.keys()
del QUIZ_DICT['failed']

for question, answers in QUIZ_DICT.items():
    # We need at least 2 options.
    assert len(answers['options']) >= 2

    # Some options are ints. However, all the answers are strings.
    # Here we check if the options are ints and then convert them to strings for validation a bit later.
    # Should we not just specify everything as strings? Or keep the types between correct and options consistent? Maybe
    # I should just read the code but that seems like effort.
    if type(answers['options'][0]) is int:
        answers['options'] = [str(item) for item in answers['options']]

    print(f"Checking: {question}")
    # Ensure the correct answer is part of the available options.
    assert answers['correct'] in answers['options']

print("Passed")
