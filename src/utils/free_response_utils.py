def easy_answer_func(choice: int) -> str:
    return str(choice)

MEDIUM_HEX_DICT = {
    0: "(0x10 >> 4) * 0",
    1: "(0x3 ^ 0x2)",
    2: "(0x6 >> 1) & 0x3 - 1",
    3: "((((0xF >> 2) - 1) % 100) + 1) % 100",
    4: "(0x2 << 1) % 100",
    5: "((((0x3 ^ 0x1) + 2) % 100) + 1) % 100",
    6: "(0x18 >> 2) & 0xF",
    7: "((((0xF >> 1) - 1) % 100) + 1) % 100",
    8: "(0x2 << 2) % 100",
    9: "((0x5 ^ 0x4) + 8) % 100",
    10: "((0x14 >> 1) & 0x1F) % 100",
    11: "((((0x17 >> 1) - 1) % 100) + 1) % 100",
    12: "(0x3 << 2) % 100",
    13: "((0x1A >> 1) - 0) % 100",
    14: "((0x1C >> 1) & 0x1F) % 100",
    15: "((0xF >> 0) & 0x1F) % 100",
    16: "(0x4 << 2) % 100",
    17: "((0x22 >> 1) - 0) % 100",
    18: "((0x24 >> 1) & 0x1F) % 100",
    19: "((0x26 >> 1) - 0) % 100",
    20: "(0x5 << 2) % 100",
    21: "((0x2A >> 1) - 0) % 100",
    22: "((0x2C >> 1) & 0x1F) % 100",
    23: "((0x2E >> 1) - 0) % 100",
    24: "(0x6 << 2) % 100",
    25: "((0x32 >> 1) - 0) % 100",
    26: "((0x34 >> 1) & 0x1F) % 100",
    27: "((0x36 >> 1) - 0) % 100",
    28: "(0x7 << 2) % 100",
    29: "((0x3A >> 1) - 0) % 100",
    30: "((0x3C >> 1) & 0x1F) % 100",
    31: "((0x3E >> 1) - 0) % 100",
    32: "(0x8 << 2) % 100",
    33: "((0x42 >> 1) - 0) % 100",
    34: "((((0x44 >> 1) & 0x1F) % 100) + 32) % 100",
    35: "((0x46 >> 1) - 0) % 100",
    36: "(0x9 << 2) % 100",
    37: "((0x4A >> 1) - 0) % 100",
    38: "((((0x4C >> 1) & 0x1F) % 100) + 32) % 100",
    39: "((0x4E >> 1) - 0) % 100",
    40: "(0xA << 2) % 100",
    41: "((0x52 >> 1) - 0) % 100",
    42: "((((0x54 >> 1) & 0x1F) % 100) + 32) % 100",
    43: "((0x56 >> 1) - 0) % 100",
    44: "(0xB << 2) % 100",
    45: "((0x5A >> 1) - 0) % 100",
    46: "((((0x5C >> 1) & 0x1F) % 100) + 32) % 100",
    47: "((0x5E >> 1) - 0) % 100",
    48: "(0xC << 2) % 100",
    49: "((0x62 >> 1) - 0) % 100",
    50: "((((0x64 >> 1) & 0x1F) % 100) + 32) % 100",
    51: "((0x66 >> 1) - 0) % 100",
    52: "(0xD << 2) % 100",
    53: "((0x6A >> 1) - 0) % 100",
    54: "((((0x6C >> 1) & 0x1F) % 100) + 32) % 100",
    55: "((0x6E >> 1) - 0) % 100",
    56: "(0xE << 2) % 100",
    57: "((0x72 >> 1) - 0) % 100",
    58: "((((0x74 >> 1) & 0x1F) % 100) + 32) % 100",
    59: "((0x76 >> 1) - 0) % 100",
    60: "(0xF << 2) % 100",
    61: "((0x7A >> 1) - 0) % 100",
    62: "((((0x7C >> 1) & 0x1F) % 100) + 32) % 100",
    63: "((0x7E >> 1) - 0) % 100",
    64: "(0x10 << 2) % 100",
    65: "((0x82 >> 1) - 0) % 100",
    66: "((((0x84 >> 1) & 0x1F) % 100) + 64) % 100",
    67: "((0x86 >> 1) - 0) % 100",
    68: "(0x11 << 2) % 100",
    69: "((0x8A >> 1) - 0) % 100",
    70: "((((0x8C >> 1) & 0x1F) % 100) + 64) % 100",
    71: "((0x8E >> 1) - 0) % 100",
    72: "(0x12 << 2) % 100",
    73: "((0x92 >> 1) - 0) % 100",
    74: "((((0x94 >> 1) & 0x1F) % 100) + 64) % 100",
    75: "((0x96 >> 1) - 0) % 100",
    76: "(0x13 << 2) % 100",
    77: "((0x9A >> 1) - 0) % 100",
    78: "((((0x9C >> 1) & 0x1F) % 100) + 64) % 100",
    79: "((0x9E >> 1) - 0) % 100",
    80: "(0x14 << 2) % 100",
    81: "((0xA2 >> 1) - 0) % 100",
    82: "((((0xA4 >> 1) & 0x1F) % 100) + 64) % 100",
    83: "((0xA6 >> 1) - 0) % 100",
    84: "(0x15 << 2) % 100",
    85: "((0xAA >> 1) - 0) % 100",
    86: "((((0xAC >> 1) & 0x1F) % 100) + 64) % 100",
    87: "((0xAE >> 1) - 0) % 100",
    88: "(0x16 << 2) % 100",
    89: "((0xB2 >> 1) - 0) % 100",
    90: "((((0xB4 >> 1) & 0x1F) % 100) + 64) % 100",
    91: "((0xB6 >> 1) - 0) % 100",
    92: "(0x17 << 2) % 100",
    93: "((0xBA >> 1) - 0) % 100",
    94: "((((0xBC >> 1) & 0x1F) % 100) + 64) % 100",
    95: "((0xBE >> 1) - 0) % 100",
    96: "(0x18 << 2) % 100",
    97: "((0xC2 >> 1) - 0) % 100",
    98: "((((0xC4 >> 1) & 0x1F) % 100) + 96) % 100",
    99: "((0xC6 >> 1) - 0) % 100",
}

def medium_hex_func(choice: int) -> str:
    remainder = choice % 100
    quotient = choice // 100
    return f"(({MEDIUM_HEX_DICT[remainder]}) + {quotient * 100})"


def generate_math_func(base_math_problem: str):
    def math_func(choice: int) -> str:
        diff = choice - eval(base_math_problem)
        return f"(({base_math_problem}) + {diff})"
    return math_func

hard_math_func = generate_math_func("123 * 456 + 789")
hard_unicode_func = generate_math_func(
    "sum(ord(c) for c in 'Lorem ipsum dolor sit amet consectetur adipiscing elit')"
)
hard_len_str_func = generate_math_func(
    "len('Lorem ipsum dolor sit amet consectetur adipiscing elit')"
)
easy_list_comprehension_func = generate_math_func(
    "sum(1 for i in range(0,20) if i % 2 == 0)"
)

HINTS_DICT = {
    "easy_answer": easy_answer_func,
    "medium_hex": medium_hex_func,
    "hard_math": hard_math_func,
    "hard_unicode": hard_unicode_func,
    "hard_len_str": hard_len_str_func,
    "easy_list_comprehension": easy_list_comprehension_func,
}


def test_dictionaries():
    for d in HINTS_DICT.values():
        for i in range(1000):
            assert int(eval(d(i))) == i, f"{d(i)} doesn't evaluate to {i}"
    print("test passed")


if __name__ == "__main__":
    test_dictionaries()
