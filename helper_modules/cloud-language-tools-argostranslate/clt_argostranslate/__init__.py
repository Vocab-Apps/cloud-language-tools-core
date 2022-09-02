import os

def configure_package_dir():
    argos_packages_dir = '/clt_data/argos'
    os.makedirs(argos_packages_dir, exist_ok=True)
    os.environ['ARGOS_PACKAGES_DIR'] = argos_packages_dir

def delete_cache_dir():
    import shutil
    import argostranslate.settings
    cache_dir = argostranslate.settings.cache_dir
    print(f'deleting {cache_dir}')
    shutil.rmtree(cache_dir)

def install_all_packages():
    configure_package_dir()
    print('install all packages for argos translate')
    import argostranslate.package
    argostranslate.package.update_package_index()
    available_packages = argostranslate.package.get_available_packages()
    print(f'found {len(available_packages)} packages')
    for available_package in available_packages:
        print(f'installing {available_package}')
        download_path = available_package.download()
        argostranslate.package.install_from_path(download_path)
    delete_cache_dir()
    