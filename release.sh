#!/bin/zsh
rm -r ./Release-app
mkdir ./Release-app

cp ./src/DataManagement.py ./Release-app/DataManagement.py
cp ./src/Exporter.py ./Release-app/Exporter.py
cp ./src/GlobalData.py ./Release-app/GlobalData.py
cp ./src/LogManagement.py ./Release-app/LogManagement.py
cp ./src/question_manager_app.py ./Release-app/question_manager_app.py
cp ./src/main.py ./Release-app/main.py

cd ./Release-app

python -m nuitka \
          --standalone \
          --enable-plugin=pyside6 \
          --macos-create-app-bundle \
          --output-dir=build \
          --assume-yes-for-download \
          --macos-app-name=QuestionManager \
          --disable-console \
          main.py
