def install_all_packages():
    print('install all packages for spacy')
    import spacy.cli    
    spacy.cli.download('zh_core_web_trf')
    spacy.cli.download('en_core_web_trf')
    spacy.cli.download('fr_dep_news_trf')
    spacy.cli.download('ja_core_news_lg')
    spacy.cli.download('de_dep_news_trf')
    spacy.cli.download('es_dep_news_trf')
    spacy.cli.download('ru_core_news_lg')
    spacy.cli.download('pl_core_news_lg')
    spacy.cli.download('it_core_news_lg')
    