import enum

# usage/account related constants 
# ===============================

class RequestType(enum.Enum):
    translation = enum.auto()
    transliteration = enum.auto()
    audio = enum.auto()
    breakdown = enum.auto()
    dictionary = enum.auto()

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

class ServiceFee(enum.Enum):
    free = enum.auto()
    paid = enum.auto()

# what triggered this request (batch / on the fly / editor)
class RequestMode(enum.Enum):
    batch = enum.auto()
    dynamic = enum.auto()
    edit = enum.auto()

class APIVersion(enum.Enum):
    v1 = enum.auto()
    v2 = enum.auto()
    v3 = enum.auto()

# service and language related constants
# ======================================

RequestTimeout = 10 # 10 seconds max
# need to change timeout for long requests, such as retrieving list of services
RequestTimeoutLong = 20 # 10 seconds max
ReadTimeout = 3 # 3 seconds read timeout

TTLCacheTimeout = 86400 # 24 hours

class Service(enum.StrEnum):
    Azure = 'Azure'
    Google = 'Google'
    MandarinCantonese = 'MandarinCantonese'
    EasyPronunciation = 'EasyPronunciation'
    OpenAI = 'OpenAI'
    Watson = 'Watson'
    Naver = 'Naver'
    Amazon = 'Amazon'
    Forvo = 'Forvo'
    CereProc = 'CereProc'
    Epitran = 'Epitran'
    DeepL = 'DeepL'
    VocalWare = 'VocalWare'
    Voicen = 'Voicen'
    FptAi = 'FptAi'
    PyThaiNLP = 'PyThaiNLP'
    Spacy = 'Spacy'
    Wenlin =    'Wenlin'
    LibreTranslate = 'LibreTranslate'
    ElevenLabs = 'ElevenLabs'
    Alibaba = 'Alibaba'
    Gemini = 'Gemini'
    TestServiceA = 'TestServiceA'
    TestServiceB = 'TestServiceB'

class Gender(enum.StrEnum):
    Male = 'Male'
    Female = 'Female'
    Any = 'Any'


class DictionaryLookupType(enum.Enum):
    Definitions = enum.auto()
    PartOfSpeech = enum.auto()
    MeasureWord = enum.auto()
    PartOfSpeechDefinitions = enum.auto()
