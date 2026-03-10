import os, re
from lib.conf import tts_dir, voices_dir

loaded_tts = {}
xtts_builtin_speakers_list = {}

TTS_ENGINES = {
    "XTTSv2": "xtts",
    "BARK": "bark",
    "TORTOISE": "tortoise",
    "VITS": "vits",
    "FAIRSEQ": "fairseq",
    "GLOWTTS": "glowtts",
    "TACOTRON2": "tacotron",
    "YOURTTS": "yourtts"
}

TTS_VOICE_CONVERSION = {
    "freevc24": {"path": "voice_conversion_models/multilingual/vctk/freevc24", "samplerate": 24000},
    "knnvc": {"path": "voice_conversion_models/multilingual/multi-dataset/knnvc", "samplerate": 16000},
    "openvoice_v1": {"path": "voice_conversion_models/multilingual/multi-dataset/openvoice_v1", "samplerate": 22050},
    "openvoice_v2": {"path": "voice_conversion_models/multilingual/multi-dataset/openvoice_v2", "samplerate": 22050}
}

TTS_SML = {
    "break": {"static": "[break]", "paired": False},
    "pause": {"static": "[pause]", "paired": False},
    "voice": {"paired": True},
}

sml_escape_tag = 0xE000
sml_tag_keys = '|'.join(map(re.escape, TTS_SML.keys()))

SML_TAG_PATTERN = re.compile(
    rf'''
    \[
        \s*
        (?P<close>/)?
        \s*
        (?P<tag>{sml_tag_keys})
        (?:\s*:\s*(?P<value>.*?))?
        \s*
    \]
    ''',
    re.VERBOSE | re.DOTALL
)

default_tts_engine = TTS_ENGINES['XTTSv2']
default_fine_tuned = 'internal'
default_vc_model = TTS_VOICE_CONVERSION['knnvc']['path']
default_voice_detection_model = 'drewThomasson/segmentation'

max_custom_model = 100
max_custom_voices = 1000

default_engine_settings = {
    TTS_ENGINES['XTTSv2']: {
        "repo": "coqui/XTTS-v2",
        "languages": {"eng": "en"},
        "samplerate": 24000,
        "temperature": 0.75,
        #"codec_temperature": 0.3,
        "length_penalty": 1.0,
        "num_beams": 1,
        "repetition_penalty": 2.0,
        #"cvvp_weight": 0.3,
        "top_k": 40,
        "top_p": 0.95,
        "speed": 1.0,
        #"gpt_cond_len": 512,
        #"gpt_batch_size": 1,
        "enable_text_splitting": False,
        "files": ['config.json', 'model.pth', 'vocab.json', 'ref.wav'],
        "voices": {
            "ClaribelDervla": "Claribel Dervla", "DaisyStudious": "Daisy Studious", "GracieWise": "Gracie Wise",
            "TammieEma": "Tammie Ema", "AlisonDietlinde": "Alison Dietlinde", "AnaFlorence": "Ana Florence",
            "AnnmarieNele": "Annmarie Nele", "AsyaAnara": "Asya Anara", "BrendaStern": "Brenda Stern",
            "GittaNikolina": "Gitta Nikolina", "HenrietteUsha": "Henriette Usha", "SofiaHellen": "Sofia Hellen",
            "TammyGrit": "Tammy Grit", "TanjaAdelina": "Tanja Adelina", "VjollcaJohnnie": "Vjollca Johnnie",
            "AndrewChipper": "Andrew Chipper", "BadrOdhiambo": "Badr Odhiambo", "DionisioSchuyler": "Dionisio Schuyler",
            "RoystonMin": "Royston Min", "ViktorEka": "Viktor Eka", "AbrahanMack": "Abrahan Mack",
            "AddeMichal": "Adde Michal", "BaldurSanjin": "Baldur Sanjin", "CraigGutsy": "Craig Gutsy",
            "DamienBlack": "Damien Black", "GilbertoMathias": "Gilberto Mathias", "IlkinUrbano": "Ilkin Urbano",
            "KazuhikoAtallah": "Kazuhiko Atallah", "LudvigMilivoj": "Ludvig Milivoj", "SuadQasim": "Suad Qasim",
            "TorcullDiarmuid": "Torcull Diarmuid", "ViktorMenelaos": "Viktor Menelaos", "ZacharieAimilios": "Zacharie Aimilios",
            "NovaHogarth": "Nova Hogarth", "MajaRuoho": "Maja Ruoho", "UtaObando": "Uta Obando",
            "LidiyaSzekeres": "Lidiya Szekeres", "ChandraMacFarland": "Chandra MacFarland", "SzofiGranger": "Szofi Granger",
            "CamillaHolmström": "Camilla Holmström", "LilyaStainthorpe": "Lilya Stainthorpe", "ZofijaKendrick": "Zofija Kendrick",
            "NarelleMoon": "Narelle Moon", "BarboraMacLean": "Barbora MacLean", "AlexandraHisakawa": "Alexandra Hisakawa",
            "AlmaMaría": "Alma María", "RosemaryOkafor": "Rosemary Okafor", "IgeBehringer": "Ige Behringer",
            "FilipTraverse": "Filip Traverse", "DamjanChapman": "Damjan Chapman", "WulfCarlevaro": "Wulf Carlevaro",
            "AaronDreschner": "Aaron Dreschner", "KumarDahl": "Kumar Dahl", "EugenioMataracı": "Eugenio Mataracı",
            "FerranSimen": "Ferran Simen", "XavierHayasaka": "Xavier Hayasaka", "LuisMoray": "Luis Moray",
            "MarcosRudaski": "Marcos Rudaski"
        },
        "rating": {"VRAM": 4, "CPU": 2, "RAM": 4, "Realism": 5}
    },
    TTS_ENGINES['BARK']: {
        "languages": {"eng": "en"},
        "samplerate": 24000,
        "text_temp": 0.22,
        "waveform_temp": 0.44,
        "files": ["text_2.pt", "coarse_2.pt", "fine_2.pt"],
        "speakers_path": os.path.join(voices_dir, '__bark'),
        "voices": {
            "en_speaker_0": "Speaker 0", "en_speaker_1": "Speaker 1", "en_speaker_2": "Speaker 2", "en_speaker_3": "Speaker 3", "en_speaker_4": "Speaker 4", "en_speaker_5": "Speaker 5", "en_speaker_6": "Speaker 6", "en_speaker_7": "Speaker 7", "en_speaker_8": "Speaker 8", "en_speaker_9": "Speaker 9"
        },
        "rating": {"VRAM": 6, "CPU": 1, "RAM": 6, "Realism": 4}
    },
    TTS_ENGINES['TORTOISE']: {
        "languages": {"eng": "en"},
        "samplerate": 24000,
        "files": ['config.json', 'best_model.pth', 'vocoder_config.json', 'vocoder_model.pth'],
        "voices": {},
        "rating": {"VRAM": 3, "CPU": 2, "RAM": 4, "Realism": 4}
    },
    TTS_ENGINES['VITS']: {
        "languages": {"eng": "en"},
        "samplerate": 22050,
        "files": ['autoregressive.pth ', 'diffusion_decoder.pth', 'vocoder.pth', 'clvp2.pth'],
        "voices": {},
        "rating": {"VRAM": 2, "CPU": 4, "RAM": 4, "Realism": 4}
    },
    TTS_ENGINES['FAIRSEQ']: {
        "languages": {"eng": "en", "tam": "ta"},
        "samplerate": 16000,
        "files": ['config.json', 'G_100000.pth', 'vocab.json'],
        "voices": {},
        "rating": {"VRAM": 2, "CPU": 4, "RAM": 4, "Realism": 4}
    },
    TTS_ENGINES['GLOWTTS']: {
        "languages": {"eng": "en"},
        "samplerate": 22050,
        "files": ['config.json', 'best_model.pth', 'vocoder_config.json', 'vocoder_model.pth'],
        "voices": {},
        "rating": {"VRAM": 1, "CPU": 4, "RAM": 2, "Realism": 3}
    },
    TTS_ENGINES['TACOTRON2']: {
        "languages": {"eng": "en"},
        "samplerate": 22050,
        "files": ['config.json', 'model_file.pth', 'vocoder_config'],
        "rating": {"VRAM": 1, "CPU": 5, "RAM": 2, "Realism": 3}
    },
    TTS_ENGINES['YOURTTS']: {
        "languages": {"eng": "en"},
        "samplerate": 16000,
        "files": ['config.json', 'model_file.pth'],
        "voices": {"Machinella-5": "female-en-5", "ElectroMale-2": "male-en-2"},
        "rating": {"VRAM": 1, "CPU": 5, "RAM": 1, "Realism": 2}
    }
}