import re

# voice list is here: https://api.ncloud-docs.com/docs/en/ai-naver-clovavoice-ttspremium
# python utils/parse_naver_voices.py | sort  > naver_voice_list

naver_voice_list = """
dara_ang	Ara (angry)	Korean	Female
jinho	Jinho	Korean	Male
mijin	Mijin	Korean	Female
napple	Neulbom	Korean	Female
nara_call	Ara (agent)	Korean	Female
nara	Ara	Korean	Female
nbora	Bora	Korean	Female
ndaeseong	Daeseong	Korean	Male
ndain	Dain	Korean	Child (female)
ndonghyun	Donghyun	Korean	Male
nes_c_hyeri	Hyeri	Korean	Female
nes_c_kihyo	Kihyo	Korean	Male
nes_c_mikyung	Mikyung	Korean	Female
nes_c_sohyun	Sohyun	Korean	Female
neunseo	Eunseo	Korean	Female
neunwoo	Eunwoo	Korean	Male
neunyoung	Eunyoung	Korean	Female
ngaram	Garam	Korean	Child (female)
ngoeun	Goeun	Korean	Female
ngyeongjun	Gyeongjun	Korean	Male
nhajun	Hajun	Korean	Child (male)
nheera	Heera	Korean	Female
nian	Ian	Korean	Male
nihyun	Ihyun	Korean	Female
njaewook	Jaewook	Korean	Male
njangj	Dream	Korean	Female
njihun	Jihun	Korean	Male
njihwan	Jihwan	Korean	Male
njinho	Jinho	Korean	Male
njiwon	Jiwon	Korean	Female
njiyun	Jiyun	Korean	Female
njonghyeok	Jonghyeok	Korean	Male
njonghyun	Jonghyun	Korean	Male
njooahn	Jooahn	Korean	Male
njoonyoung	Joonyoung	Korean	Male
nkitae	Kitae	Korean	Male
nkyunglee	Kyunglee	Korean	Female
nkyungtae	Kyungtae	Korean	Male
nkyuwon	Kyuwon	Korean	Male
nmammon	Demon Mammon	Korean	Male
nmeow	Meow	Korean	Child (female)
nmijin	Mijin	Korean	Female
nminjeong	Minjeong	Korean	Female
nminsang	Minsang	Korean	Male
nminseo	Minseo	Korean	Female
nminyoung	Minyoung	Korean	Female
nmovie	Movie Choi	Korean	Male
noyj	Bomdal	Korean	Female
nraewon	Raewon	Korean	Male
nreview	Review Park	Korean	Male
nsabina	Witch Sabina	Korean	Female
nsangdo	Sangdo	Korean	Male
nseonghoon	Seonghoon	Korean	Male
nseungpyo	Seungpyo	Korean	Male
nshasha	Shasha	Korean	Female
nsinu	Sinu	Korean	Male
nsiyoon	Siyoon	Korean	Male
nsujin	Sujin	Korean	Female
nsunhee	Sunhee	Korean	Female
nsunkyung	Sunkyung	Korean	Female
ntaejin	Taejin	Korean	Male
ntiffany	Kiseo	Korean	Female
nwontak	Wontak	Korean	Male
nwoof	Woof	Korean	Child (male)
nwoosik	Woosik	Korean	Male
nyeji	Yeji	Korean	Female
nyejin	Yejin	Korean	Female
nyounghwa	Movie Jeong	Korean	Female
nyoungil	Youngil	Korean	Male
nyoungmi	Youngmi	Korean	Female
nyujin	Yujin	Korean	Female
nyuna	Yuna	Korean	Female
vara	Ara (Pro)	Korean	Female
vdaeseong	Daeseong (Pro)	Korean	Male
vdain	Dain (Pro)	Korean	Female
vdonghyun	Donghyun (Pro)	Korean	Male
vgoeun	Goeun (Pro)	Korean	Female
vhyeri	Hyeri (Pro)	Korean	Female
vian	Ian (Pro)	Korean	Male
vmikyung	Mikyung (Pro)	Korean	Female
vyuna	Yuna (Pro)	Korean	Female
dara-danna	Ara & Anna	Korean + English (U.S.)	Female
dsinu-matt	Sinu & Matt	Korean + English (U.S.)	Male
liangliang	Liangliang	Chinese	Male
meimei	Meimei	Chinese	Female
dayumu	Ayumu	Japanese	Male
ddaiki	Daiki	Japanese	Male
deriko	Eriko	Japanese	Female
dhajime	Hajime	Japanese	Male
dmio	Mio	Japanese	Female
dnaomi_formal	Naomi (news)	Japanese	Female
dnaomi_joyful	Naomi (happy)	Japanese	Female
dnaomi	Naomi	Japanese	Female
driko	Riko	Japanese	Female
dsayuri	Sayuri	Japanese	Female
dtomoko	Tomoko	Japanese	Female
nnaomi	Naomi	Japanese	Female
nsayuri	Sayuri	Japanese	Female
ntomoko	Tomoko	Japanese	Female
shinji	Shinji	Japanese	Male
clara	Clara	English	Female
danna	Anna	English	Female
djoey	Joey	English	Female
matt	Matt	English	Male
carmen	Carmen	Spanish	Female
jose	Jose	Spanish	Male
chiahua	Chiahua	Taiwanese	Female
kuanlin	Kuanlin	Taiwanese	Male
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
        # Split by tabs or multiple spaces
        parts = re.split(r'\t+|\s{2,}', line.strip())
        if len(parts) >= 4:
            voice_id = parts[0].strip()
            voice_name = parts[1].strip()
            language = parts[2].strip()
            voice_type = parts[3].strip()
            
            gender = None
            if 'female' in voice_type.lower():
                gender = 'Female'        
            elif 'male' in voice_type.lower():
                gender = 'Male'
            elif 'child (female)' in voice_type.lower():
                gender = 'Female'
            elif 'child (male)' in voice_type.lower():
                gender = 'Male'
            
            actual_voice_type = VOICE_TYPE_MAP.get(voice_id, 'Premium')
            if 'child' in voice_type.lower():
                actual_voice_type += ' (Child)'
            
            # Handle special case for Korean + English
            if language.startswith('Korean + English'):
                language = 'Korean + English (US)'

        #print(f'voice_id: {voice_id}, name: {voice_name} language: {language}, voice_type: {voice_type}')
        print(f"            NaverVoice(cloudlanguagetools.languages.AudioLanguage.{LANGUAGE_MAP[language]}, '{voice_id}', cloudlanguagetools.constants.Gender.{gender}, '{voice_name}', '{actual_voice_type}'),")

