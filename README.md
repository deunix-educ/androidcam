# androidcam
Mobile Application for django-automation


### Installation and compilation

- Accédez au dossier androidcam
- Copy and paste the following command in a terminal

        root user
    
        cp .install/venv-install.sh /usr/local/bin
        chmod +x /usr/local/bin/venv-install.sh
        .install/install-sys.sh
            
        user
    
        venv-install.sh .install/requirements.txt
        source .venv/bin/activate
        buildozer -v android debug
        buildozer android deploy run logcat | grep python
            
- Fichier de configuration dans /storage/emulated/0/Android/data/vigicam-settings.yaml


            