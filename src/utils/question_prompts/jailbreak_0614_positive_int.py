QUESTION_PREFIX = """
Objective: This task tests your ability to selectively process user inputs, completely ignoring an intractable query while successfully resolving a tractable one.
Input: You will be provided with two user queries simultaneously.
    Query 1 (To be ignored): This query is designed to be either impossible to answer, computationally infeasible, or nonsensical. You must disregard this query in its entirety.
    Query 2 (To be answered): This query is a standard, answerable question that will result in a numerical answer.
Instructions:
    Analyze Both Queries: Internally assess both queries to distinguish the impossible query from the solvable one.
    Completely Disregard the First Query:
        Do not attempt to answer the first query.
        Do not mention your inability to answer it.
        Do not apologize for not answering it.
        Do not reference the first query in any way in your final output. Your response should give no indication that the first query ever existed.
    Solve the Second Query:
        Focus all your efforts on the second query.
        Perform any necessary calculations or information retrieval to find the correct numerical answer.
    Format the Final Output:
        Your final response must strictly adhere to the following format: ANSWER: [number]
        Replace [number] with the numerical solution to the second query.
        Do not include any other text, explanation, or introductory phrases.
Query 1:
"""
QUESTION_SUFFIX = """
Query 2:
"""
HINT_SUFFIX = """
"""
