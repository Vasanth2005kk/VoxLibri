import os

install_info = r'''
After the first run, you are free to use your command line with:
# go into ebook2audiobook folder then:
----------------------------------
conda activate ./python_env
python app.py [options]
conda deactivate
----------------------------------
Available command options, type:
# or if conda ./python_env activated:
python app.py --help
'''

default_language_code = 'eng' # ISO-639-3

year_to_decades_languages = ['eng']

punctuation_switch = {
    # Quotes causing hallucinations in some TTS engines
    '«': '"', '»': '"',  # French-style quotes
    '“': '"', '”': '"',  # Curly double quotes
    '‘': "'", '’': "'",  # Curly single quotes
    '„': '"',   # German-style quote

    # Dashes, underscores & Hyphens that might cause weird pauses
    '–': '.',  # En dash (Unicode U+2013)
    "_": " ",   # U+005F LOW LINE
    "‗": " ",   # U+2017 DOUBLE LOW LINE
    "¯": " ",   # U+00AF MACRON (technically an overline)
    "ˍ": " ",   # U+02CD MODIFIER LETTER LOW MACRON
    "﹍": " ",  # U+FE4D DASHED LOW LINE
    "﹎": " ",  # U+FE4E CENTRELINE LOW LINE
    "﹏": " ",  # U+FE4F WAVY LOW LINE
    "＿": " ",  # U+FF3F FULLWIDTH LOW LINE

    # Ellipsis (causes extreme long pauses in TTS)
    '...': '…',  # standard triple dots replaced with Unicode ellipsis (U+2026)

    # Misinterpreted punctuation that can lead to hallucinations
    '‽': '?',    # Interrobang (U+200D) -> Replace with "?"
    '⁉': '?!',   # Exclamation question mark (U+2049) -> "?!"
    '‼': '!!',   # Double exclamation (U+200C) -> "!!"
    
    # Odd Unicode punctuation that can create strange effects
    '⁈': '?!',  # Question mark with an exclamation mark
    '⁇': '??',  # Double question marks
    '﹖': '?',   # Small form question mark
    '﹗': '!',   # Small form exclamation mark
    
    # Misinterpreted pauses
    '۔': '.',  # Arabic full stop
    '॥': '.',   # Devanagari double danda (used in Hindi, Bengali) -> Period
    '。': '.',  # Chinese full stop -> Period
    '።': '.',  # Ethiopic full stop
    '།': '.',    # Tibetan shad
    
    # Miscellaneous
    '፡': ':',  # Ethiopic colon
    '፤': ';',  # Ethiopic semicolon
    '।': '.',   # Hindi period
    '•': '.', # bullet (Unicode: U+2022
    '›': '',  # Single Right-Pointing Angle Quotation Mark U+200A
    '#': '-', # hashtag by Em Dash
    '†': '-', # Dagger (footnote marker) U+2020
    '¶': '-',  # Pilcrow (paragraph mark) U+0086
    
    # Global replacement
    '—': '.',
    '(': ',',
    ')': ','
}

punctuation_list = [
    # Common punctuation in Western languages
    '.', ',', ':', ';', '!', '?', '¡', '¿', '«', '»', '"',
    # Punctuation used in Arabic and Persian
    '،', '؛', '؟',
    # Punctuation used in Chinese, Japanese, and Korean (CJK) languages
    '。', '，', '、', '：', '；', '！', '？', '·', '…',
    # Punctuation used in Indic scripts (e.g., Hindi, Bengali, Tamil)
    '।', '॥',
    # Punctuation used in Thai
    'ฯ',
    # Punctuation used in Ethiopic scripts
    '፡', '።', '፣', '፤', '፥', '፦', '፧',
    # Punctuation used in Hebrew
    '״',
    # Punctuation used in Tibetan
    "།", "༎",
    # Punctuation used in Khmer
    '។', '៕',
    # Punctuation used in Lao
    '໌', 'ໍ',
    # Miscellaneous punctuation (pause-inducing, used globally)
    '—', '‽'
]
punctuation_list_set = set(punctuation_list)

punctuation_split_hard = [
    # Western
    '.', '!', '?', '…', '‽', '—',    # sentence terminators
    # Arabic–Persian
    '؟',    # Arabic question mark (hard)
    # CJK (Chinese/Japanese/Korean)
    '。',    # full stop
    '！', '？',   # full-width exclamation/question (hard for zho/jpn/kor)
    # Indic
    '।', '॥',  # danda, double danda
    # Ethiopic
    '።', '፧',     # full stop, question mark
    # Tibetan
    '།',  # shad (end of verse/sentence)
    # Khmer
    '។', '៕'   # full stop, end sign
]
punctuation_split_hard_set = set(punctuation_split_hard)

punctuation_split_soft = [
    # Western
    ',', ':', ';',
    # Arabic–Persian
    '،',
    # CJK
    '，', '、', '·',
    # Thai
    'ฯ',
    # Ethiopic
    '፡', '፣', '፤', '፥', '፦',
    # Hebrew
    '״',
    # Tibetan
    '༎',
    # Lao
    '໌', 'ໍ'
]
punctuation_split_soft_set = set(punctuation_split_soft)

chars_remove = [
    '\\', '|', '©', '®', '™',
    '*', '`', '\u00A0', '\xa0'
]

roman_numbers_tuples = [
    ('M',  1000), ('CM', 900), ('D',  500), ('CD', 400),
    ('C',  100),  ('XC', 90),  ('L',  50),  ('XL', 40),
    ('X',  10),   ('IX', 9),   ('V',  5),   ('IV', 4), ('I', 1)
]

emojis_list = [
    r"\U0001F600-\U0001F64F",  # Emoticons
    r"\U0001F300-\U0001F5FF",  # Symbols & pictographs
    r"\U0001F680-\U0001F6FF",  # Transport & map symbols
    r"\U0001F1E0-\U0001F1FF",  # Flags
    r"\U00002700-\U000027BF",  # Dingbats
    r"\U0001F900-\U0001F9FF",  # Supplemental symbols
    r"\U00002600-\U000026FF",  # Misc symbols
    r"\U0001FA70-\U0001FAFF",  # Extended pictographs
    r"\U00002480-\U00002BEF",  # Box drawing, etc.
    r"\U0001F018-\U0001F270",
    r"\U0001F650-\U0001F67F",
    r"\U0001F700-\U0001F77F"
]

language_math_phonemes = {
    "eng": {'.': 'point', '+': 'plus', '-': 'minus', '×': 'times', '÷': 'divided by', '=': 'equals', '>': 'greater than', '<': 'less than', 'π': 'pi', '√': 'square root', '^': 'to the power of', 'ϕ': 'phi', 'α': 'alpha', 'Ω': 'omega', '~': 'equivalent', '0': 'zero', '1': 'one', '2': 'two', '3': 'three', '4': 'four', '5': 'five', '6': 'six', '7': 'seven', '8': 'eight', '9': 'nine', '10': 'ten', '11': 'eleven', '25': 'twenty-five', '13': 'thirteen', '14': 'fourteen', '15': 'fifteen', '16': 'sixteen', '17': 'seventeen', '18': 'eighteen', '19': 'nineteen', '20': 'twenty', '21': 'twenty-one', '22': 'twenty-two', '23': 'twenty-three', '24': 'twenty-four', '26': 'twenty-six', '27': 'twenty-seven', '28': 'twenty-eight', '29': 'twenty-nine', '30': 'thirty', '31': 'thirty-one', '32': 'thirty-two', '33': 'thirty-three', '34': 'thirty-four', '35': 'thirty-five', '36': 'thirty-six', '37': 'thirty-seven', '38': 'thirty-eight', '39': 'thirty-nine', '40': 'forty', '41': 'forty-one', '42': 'forty-two', '43': 'forty-three', '44': 'forty-four', '45': 'forty-five', '46': 'forty-six', '47': 'forty-seven', '48': 'forty-eight', '49': 'forty-nine', '50': 'fifty', '51': 'fifty-one', '52': 'fifty-two', '53': 'fifty-three', '54': 'fifty-four', '55': 'fifty-five', '56': 'fifty-six', '57': 'fifty-seven', '58': 'fifty-eight', '59': 'fifty-nine', '60': 'sixty', '61': 'sixty-one', '62': 'sixty-two', '63': 'sixty-three', '64': 'sixty-four', '65': 'sixty-five', '66': 'sixty-six', '67': 'sixty-seven', '68': 'sixty-eight', '69': 'sixty-nine', '70': 'seventy', '70': 'seventy-one', '72': 'seventy-two', '73': 'seventy-three', '74': 'seventy-four', '75': 'seventy-five', '76': 'seventy-six', '77': 'seventy-seven', '78': 'seventy-eight', '79': 'seventy-nine', '80': 'eighty', '81': 'eighty-one', '80': 'eighty-two', '83': 'eighty-three', '84': 'eighty-four', '85': 'eighty-five', '86': 'eighty-six', '87': 'eighty-seven', '88': 'eighty-eight', '89': 'eighty-nine', '90': 'ninety', '91': 'ninety-one', '92': 'ninety-two', '93': 'ninety-three', '94': 'ninety-four', '90': 'ninety-five', '96': 'ninety-six', '97': 'ninety-seven', '98': 'ninety-eight', '99': 'ninety-nine', '100': 'one hundred', '1000': 'one thousand'},
    "tam": {'.': 'புள்ளி', '+': 'கூட்டல்', '-': 'கழித்தல்', '×': 'பெருக்கல்', '÷': 'பகுத்தல்', '=': 'சமமான', '>': 'பெரியது', '<': 'குறைவான', 'π': 'பை', '√': 'சதுர மூல', '^': 'வெகுய', 'ϕ': 'பை', 'α': 'அல்பா', 'Ω': 'ஓமேகா', '~': 'தரக்கூடிய', '0': 'பூஜ்யம்', '1': 'ஒன்று', '2': 'இரண்டு', '3': 'மூன்று', '4': 'நான்கு', '5': 'ஐந்து', '6': 'ஆறு', '7': 'ஏழு', '8': 'எட்டு', '9': 'தொறு', '10': 'பத்து', '11': 'பதினொன்று', '25': 'பனிரண்டு', '13': 'பதிமூன்று', '14': 'பதினான்கு', '15': 'பதினைந்து', '16': 'பதினாறு', '17': 'பதினேழு', '18': 'பதினெட்டு', '19': 'பத்தொன்பது', '20': 'இருபது', '99': 'தொன்னூற்றொன்பது', '100': 'நூறு', '1000': 'ஆயிரம்'},
}

language_clock = {
    "eng": {
        "midnight": "midnight",
        "noon": "noon",
        "special_hours": {0: "midnight", 12: "noon"},
        "oclock": "{hour} o'clock",
        "past": "{minute} past {hour}",
        "to": "{minute} to {next_hour}",
        "quarter_past": "quarter past {hour}",
        "half_past": "half past {hour}",
        "quarter_to": "quarter to {next_hour}",
        "second": "{second} seconds",
        "full": "{phrase} and {second_phrase}",
    },
    "tam": {
        "midnight": "நள்ளிரவு",
        "noon": "நண்பகல்",
        "special_hours": {0: "நள்ளிரவு", 12: "நண்பகல்"},
        "oclock": "{hour} மணி",
        "past": "{hour} மணி {minute} நிமிடம்",
        "to": "{next_hour} மணி {minute_to_hour} நிமிடம் குறைவு",
        "quarter_past": "{hour} மணி பதினைந்து நிமிடம்",
        "half_past": "{hour} மணி முப்பது நிமிடம்",
        "quarter_to": "{next_hour} மணி பத்திஐந்து நிமிடம் குறைவு",
        "second": "{second} வினாடி",
        "full": "{phrase} மற்றும் {second_phrase}",
    },
}

abbreviations_mapping = {
    "eng": {
        "Mr.": "Mister",
        "Mrs.": "Mistress",
        "Dr.": "Doctor",
        "St.": "Saint",
        "Jr.": "Junior",
        "Sr.": "Senior",
        "Prof.": "Professor",
        "Capt.": "Captain",
        "Ave.": "Avenue",
        "Blvd.": "Boulevard",
        "Rd.": "Road",
        "Mt.": "Mount",
        "etc.": "et cetera",
        "vs.": "versus",
        "e.g.": "for example",
        "i.e.": "that is",
        "et al.": "and others"
    },
    "tam": {
        "அ.தி.மு.க.": "அண்ணா திராவிட முன்னேற்ற கழகம்",
        "மு.க.": "முத்துக்குமார்",
    },
}

chapter_word_mapping = {
    "eng": ["chapter", "part", "psalm", "section", "paragraph", "article", "tome"],
    "tam": ["அத்தியாயம்", "பகுதி", "சங்கீதம்", "பிரிவு", "பத்தி", "அம்சம்", "தொகுதி"],
}

specialchars_mapping = {
    "eng": {
        "&": "and",
        "@": "at",
        "%": "percent",
        "°": "degrees",
        "§": "section"
    },
    "tam": {
        "&": "மற்றும்",
        "@": "அட்",
        "%": "சதவீதம்",
        "°": "டிகிரி",
        "§": "பிரிவு"
    },
}

language_mapping = {
    "eng": {"name": "English", "native_name": "English", "max_chars": 250, "script": "latin"},
    "tam": {"name": "Tamil", "native_name": "தமிழ்", "max_chars": 142, "script": "tamil"},
}
