import re

naver_voice_list = """
    nara : Ara: Korean, female voice
    nara_call : Ara (agent): Korean, female voice
    nminyoung : Minyoung: Korean, female voice
    nyejin : Yejin: Korean, female voice
    mijin : Mijin: Korean, female voice
    jinho : Jinho: Korean, male voice
    clara : Clara: English, female voice
    matt : Matt: English, male voice
    shinji : Shinji: Japanese, male voice
    meimei : Meimei: Chinese, female voice
    liangliang : Liangliang: Chinese, male voice
    jose: Jose: Spanish, male voice
    carmen: Carmen: Spanish, female voice
    nminsang: Minsang: Korean, male voice
    nsinu: Shinwoo: Korean, male voice
    nhajun: Hajun: Korean, child voice (male)
    ndain: Dain: Korean, child tone (female)
    njiyun : Jiyun: Korean, female voice
    nsujin : Sujin: Korean, female voice
    njinho : Jinho: Korean, male voice
    njihun : Jihun: Korean, male voice
    njooahn : Jooan: Korean, male voice
    nseonghoon : Seonghun: Korean, male voice
    njihwan : Jihwan: Korean, male voice
    nsiyoon : Siyoon: Korean, male voice
    ngaram : Garam: Korean, children's voice (female)
    ntomoko : Tomoko: Japanese, female voice
    nnaomi : Naomi: Japanese, female voice
    dnaomi_joyful : Naomi (joy): Japanese, female voice
    dnaomi_formal : Naomi (news): Japanese, female voice
    driko : Riko: Japanese, female voice
    deriko : Eriko: Japanese, female voice
    nsayuri : Sayuri: Japanese, female voice
    ngoeun : Goeun: Korean, female voice
    neunyoung : Eunyoung : Korean, female voice
    nsunkyung : Seonkyung: Korean, female voice
    nyujin : Yujin: Korean, female voice
    ntaejin : Taejin: Korean, male voice
    nyoungil : Youngil: Korean, male voice
    nseungpyo : Seungpyo: Korean, male voice
    nwontak : Wontak: Korean, male voice
    dara_ang : Ara (angry): Korean, female voice
    nsunhee : Seonhee: Korean, female voice
    nminseo : Minseo: Korean, female voice
    njiwon: Jiwon: Korean, female voice
    nbora: Bora: Korean, female voice
    njonghyun: Jonghyun: Korean, male voice
    njoonyoung: Junyoung: Korean, male voice
    njaewook: Jaewook: Korean, male voice
    danna: Anna: English, female voice
    djoey : Joy: English, female voice
    dhajime: Hajime: Japanese, male voice
    ddaiki: Daiki: Japanese, male voice
    dayumu: Ayumu: Japanese, male voice
    dmio: Mio: Japanese, female voice
    chiahua: Chahwa: Taiwanese, female voice
    kuanlin: Guanlin: Taiwanese, male voice
    nes_c_hyeri: Hyeri: Korean, female voice
    nes_c_sohyun: Sohyeon: Korean, female voice
    nes_c_mikyung: Mikyung: Korean, female voice
    nes_c_kihyo: Kihyo: Korean, male voice
    ntiffany: Giseo: Korean, female voice
    napple: Neulbom: Korean, female voice
    njangj: Dream: Korean, female voice
    noyj: Bomdal: Korean, female voice
    neunseo: Eunseo: Korean, female voice
    nheera: Heera: Korean, female voice
    nyoungmi: Youngmi: Korean, female voice
    nnarae: Narae: Korean, female voice
    nyeji: Yeji: Korean, female voice
    nyuna: Yuna: Korean, female voice
    nkyunglee: Kyungri: Korean, female voice
    nminjeong: Minjeong: Korean, female voice
    nihyun: Lee Hyun: Korean, female voice
    nraewon: Raewon: Korean, male voice
    nkyuwon: Gyuwon: Korean, male voice
    nkitae: Kitae: Korean, male voice
    neunwoo: Eunwoo: Korean, male voice
    nkyungtae: Gyeongtae: Korean, male voice
    nwoosik: Woosik: Korean, male voice
    vara: Ara: Korean, female voice
    vmikyung: Mikyung: Korean, female voice
    vdain: Dain: Korean, female voice
    vyuna: Yuna: Korean, female voice
    vhyeri : Hyeri: Korean, female voice
    dara-danna: Ara&Anna: Korean + English (US), female voice
    dsinu-matt: Shinwoo & Matt: Korean + English (US), male voice
"""

LANGUAGE_MAP = {
    'Korean': 'ko_KR',
    'English': 'en_US',
    'Japanese': 'ja_JP',
    'Chinese': 'zh_CN',
    'Taiwanese': 'zh_TW',
    'Spanish': 'es_ES',
    'Korean + English (US)': 'ko_KR',
}

for line in naver_voice_list.splitlines():
    if len(line) > 1:
        # print(f'[{line}]')
        m = re.match('\s*([^:]+): ([^:]+): ([^,]+), (.+)', line)
        if m == None:
            raise Exception(f'could not parse {line}')
        voice_id = m.group(1)
        voice_name = m.group(2)
        language = m.group(3)
        voice_type = m.group(4)
        #print(f'voice_id: {voice_id}, name: {voice_name} language: {language}, voice_type: {voice_type}')
        print(f"NaverVoice(cloudlanguagetools.languages.AudioLanguage.{LANGUAGE_MAP[language]}, '{voice_id}', cloudlanguagetools.constants.Gender.Female, '{voice_name}', 'Premium'),")

