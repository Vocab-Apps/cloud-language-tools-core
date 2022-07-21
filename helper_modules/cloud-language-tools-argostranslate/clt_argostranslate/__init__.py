def install_all_packages():
    print('install all packages for argos translate')
    import argostranslate.package
    argostranslate.package.update_package_index()
    available_packages = argostranslate.package.get_available_packages()
    print(f'found {len(available_packages)} packages')
    for available_package in available_packages:
        print(f'installing {available_package}')
        download_path = available_package.download()
        argostranslate.package.install_from_path(download_path)
    