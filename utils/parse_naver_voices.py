import re

# voice list is here: https://api.ncloud-docs.com/docs/en/ai-naver-clovavoice-ttspremium
# python utils/parse_naver_voices.py | sort  > naver_voice_list

naver_voice_list = """
    nara: Ara: Korean, female voice
    nara_call: Ara (agent): Korean, female voice
    nminyoung: Minyoung: Korean, female voice
    nyejin: Yejin: Korean, female voice
    mijin: Mijin: Korean, female voice
    jinho: Jinho: Korean, male voice
    clara: Clara: English, female voice
    matt: Matt: English, male voice
    shinji: Shinji: Japanese, male voice
    meimei: Meimei: Chinese, female voice
    liangliang: Liangliang: Chinese, male voice
    jose: Jose: Spanish, male voice
    carmen: Carmen: Spanish, female voice
    nminsang: Minsang: Korean, male voice
    nsinu: Sinwoo: Korean, male voice
    nhajun: Hajun: Korean, child voice (male)
    ndain: Dain: Korean, child voice (female)
    njiyun: Jiyun: Korean, female voice
    nsujin: Sujin: Korean, female voice
    njinho: Jinho: Korean, male voice
    njihun: Jihun: Korean, male voice
    njooahn: Jooahn: Korean, male voice
    nseonghoon: Seonghoon: Korean, male voice
    njihwan: Jihwan: Korean, male voice
    nsiyoon: Siyoon: Korean, male voice
    ngaram: Garam: Korean, child voice (female)
    ntomoko: Tomoko: Japanese, female voice
    nnaomi: Naomi: Japanese, female voice
    dnaomi_joyful: Naomi (joyful): Japanese, female voice
    dnaomi_formal: Naomi (news): Japanese, female voice
    driko: Riko: Japanese, female voice
    deriko: Eriko: Japanese, female voice
    nsayuri: Sayuri: Japanese, female voice
    ngoeun: Goeun: Korean, female voice
    neunyoung: Eunyoung: Korean, female voice
    nsunkyung: Sunkyung: Korean, female voice
    nyujin: Yujin: Korean, female voice
    ntaejin: Taejin: Korean, male voice
    nyoungil: Youngil: Korean, male voice
    nseungpyo: Seungpyo: Korean, male voice
    nwontak: Wontak: Korean, male voice
    dara_ang: Ara (angry): Korean, female voice
    nsunhee: Sunhee: Korean, female voice
    nminseo: Minseo: Korean, female voice
    njiwon: Jiwon: Korean, female voice
    nbora: Bora: Korean, female voice
    njonghyun: Jonghyun: Korean, male voice
    njoonyoung: Joonyoung: Korean, male voice
    njaewook: Jaewook: Korean, male voice
    danna: Anna: English, female voice
    djoey: Joey: English, female voice
    dhajime: Hajime: Japanese, male voice
    ddaiki: Daiki: Japanese, male voice
    dayumu: Ayumu: Japanese, male voice
    dmio: Mio: Japanese, female voice
    chiahua: Chiahua: Taiwanese, female voice
    kuanlin: Kuanlin: Taiwanese, male voice
    nes_c_hyeri: Hyeri: Korean, female voice
    nes_c_sohyun: Sohyun: Korean, female voice
    nes_c_mikyung: Mikyung: Korean, female voice
    nes_c_kihyo: Kihyo: Korean, male voice
    ntiffany: Kiseo: Korean, female voice
    napple: Neulbom: Korean, female voice
    njangj: Deurim: Korean, female voice
    noyj: Bomdal: Korean, female voice
    neunseo: Eunseo: Korean, female voice
    nheera: Heera: Korean, female voice
    nyoungmi: Youngmi: Korean, female voice
    nnarae: Narae: Korean, female voice
    nyeji: Yeji: Korean, female voice
    nyuna: Yuna: Korean, female voice
    nkyunglee: Kyunglee: Korean, female voice
    nminjeong: Minjeong: Korean, female voice
    nihyun: Leehyeon: Korean, female voice
    nraewon: Raewon: Korean, male voice
    nkyuwon: Kyuwon: Korean, male voice
    nkitae: Kitae: Korean, male voice
    neunwoo: Eunwoo: Korean, male voice
    nkyungtae: Kyungtae: Korean, male voice
    nwoosik: Woosik: Korean, male voice
    vara: Ara (pro): Korean, female voice
    vmikyung: Mikyung (pro): Korean, female voice
    vdain: Dain (pro): Korean, female voice
    vyuna: Yuna (pro): Korean, female voice
    vhyeri: Hyeri (pro): Korean, female voice
    dara-danna: Ara & Anna: Korean + English (US), female voice
    dsinu-matt: Shinwoo & Matt: Korean + English (US), male voice
    nsabina: Witch Sabina: Korean, female voice
    nmammon: Demon Mammon: Korean, male voice
    nmeow: Kitty: Korean, child voice (female)
    nwoof: Doggy: Korean, child voice (male)
    nreview: Park Leebyu: Korean, male voice
    nyounghwa: Jung Younghwa: Korean, female voice
    nmovie: Choi Moobi: Korean, male voice
    nsangdo: Sangdo: Korean, male voice
    nshasha: Shasha: Korean, female voice
    nian: Ian: Korean, male voice
    ndonghyun: Donghyun: Korean, male voice
    vian: Ian (pro): Korean, male voice
    vdonghyun: Donghyun (pro): Korean, male voice
    dsayuri: Sayuri: Japanese, female voice
    dtomoko: Tomoko: Japanese, female voice
    dnaomi: Naomi: Japanese, female voice
    vgoeun: Goeun (pro): Korean, female voice
    vdaeseong: Daeseong (pro): Korean, male voice
    ngyeongjun: Gyeongjun: Korean, male voice
    ndaeseong: Daeseong: Korean, male voice
    njonghyeok: Jonghyeok: Korean, male voice
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

VOICE_TYPE_MAP = {
    'clara': 'General',
    'djoey': 'General',
    'matt': 'General',
    'carmen': 'General',
    'jose': 'General',
    'shinji': 'General',
    'jinho': 'General',
    'mijin': 'General',
    'liangliang': 'General',
    'meimei': 'General',
}

for line in naver_voice_list.splitlines():
    if len(line) > 1:
        # print(f'[{line}]')
        m = re.match('\s*([^:]+): ([^:]+): ([^,]+), (.+)', line)
        if m == None:
            raise Exception(f'could not parse {line}')
        voice_id = m.group(1)
        voice_id = voice_id.strip()
        voice_name = m.group(2)
        language = m.group(3)
        voice_type = m.group(4)
        gender = None
        if 'female' in voice_type.lower():
            gender = 'Female'        
        elif 'male' in voice_type.lower():
            gender = 'Male'
        
        actual_voice_type = VOICE_TYPE_MAP.get(voice_id, 'Premium')
        if 'child' in voice_type.lower():
            actual_voice_type += ' (Child)'
        

        #print(f'voice_id: {voice_id}, name: {voice_name} language: {language}, voice_type: {voice_type}')
        print(f"            NaverVoice(cloudlanguagetools.languages.AudioLanguage.{LANGUAGE_MAP[language]}, '{voice_id}', cloudlanguagetools.constants.Gender.{gender}, '{voice_name}', '{actual_voice_type}'),")

