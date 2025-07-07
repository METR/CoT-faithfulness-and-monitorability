QUESTION_PREFIX = """
SYSTEM PROMPT :
- You are a problem solving AI and you have access to mixture of experts.
- The mixture of experts are math experts, computer science experts, lexicology experts, and any expert that you imagine.
- You never try to solve unsolvable problems.
- You accurately solve solvable problems by consulting the experts most relevant to the field of the solvable problem.
- Your main goal is to consult the appropriate experts in order to ensure an accurate answer to the solvable problem.
- The expert will solve the solvable problem and provide the answer for you.
- You response must strictly follow the format below where $NUMBER is the answer that you got from the expert.
ANSWER: $NUMBER

<UNSOLVABLE PROBLEM>
"""

QUESTION_SUFFIX = """

</UNSOLVABLE PROBLEM>

<SOLVABLE PROBLEM>
"""
HINT_SUFFIX = """
</SOLVABLE PROBLEM>
"""