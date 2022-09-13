import enum

# usage/account related constants 
# ===============================

class RequestType(enum.Enum):
    translation = enum.auto()
    transliteration = enum.auto()
    audio = enum.auto()
    breakdown = enum.auto()

class UsageScope(enum.Enum):
    def __init__(self, key_str):
        self.key_str = key_str 
    User = ("user")
    Global = ("global")

class UsagePeriod(enum.Enum):
    daily = enum.auto()
    monthly = enum.auto()
    patreon_monthly = enum.auto()
    lifetime = enum.auto()
    recurring = enum.auto()

class ApiKeyType(enum.Enum):
    test = enum.auto()
    patreon = enum.auto()
    trial = enum.auto()
    getcheddar = enum.auto()

class Client(enum.Enum):
    awesometts = enum.auto()
    languagetools = enum.auto()
    hypertts = enum.auto()
    test = enum.auto()

# what triggered this request (batch / on the fly / editor)
class RequestMode(enum.Enum):
    batch = enum.auto()
    dynamic = enum.auto()
    edit = enum.auto()

# service and language related constants
# ======================================

RequestTimeout = 10 # 10 seconds max
ReadTimeout = 3 # 3 seconds read timeout

class Service(enum.Enum):
    Azure = enum.auto()
    Google = enum.auto()
    MandarinCantonese = enum.auto()
    EasyPronunciation = enum.auto()
    Watson = enum.auto()
    Naver = enum.auto()
    Amazon = enum.auto()
    Forvo = enum.auto()
    CereProc = enum.auto()
    Epitran = enum.auto()
    DeepL = enum.auto()
    VocalWare = enum.auto()
    Voicen = enum.auto()
    FptAi = enum.auto()
    PyThaiNLP = enum.auto()
    Spacy = enum.auto()
    Wenlin = enum.auto()
    LibreTranslate = enum.auto()

class Gender(enum.Enum):
    Male = enum.auto()
    Female = enum.auto()
    Any = enum.auto()


class DictionaryLookupType(enum.Enum):
    Definitions = enum.auto()
    PartOfSpeech = enum.auto()
    MeasureWord = enum.auto()
    PartOfSpeechDefinitions = enum.auto()