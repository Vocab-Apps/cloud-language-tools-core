alias tests_all='CLOUDLANGUAGETOOLS_CORE_TEST_UNRELIABLE=yes pytest tests'
alias tests_fast='pytest -n24 --dist=load tests'
alias test_audio_mandarin_azure='pytest tests/test_audio.py -k test_mandarin_azure'
alias package='./package.sh'
