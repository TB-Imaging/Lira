#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )" # get current directory
python3 -m venv $DIR/venv
source $DIR/venv/bin/activate
pip install -r $DIR/requirements.txt

echo "[Desktop Entry]" > Lira.desktop
echo "Version=1.0" >> Lira.desktop
echo "Type=Application" >> Lira.desktop
echo "Terminal=false" >> Lira.desktop
echo "Icon[en_US]=$DIR/icons/xdiagnose-lira.png" >> Lira.desktop
echo "Exec=$DIR/lira.sh" >> Lira.desktop
echo "Name[en_US]=Lira" >> Lira.desktop
echo "Comment[en_US]=Launch L.I.R.A." >> Lira.desktop
echo "Name=Lira" >> Lira.desktop
echo "Comment=Launch L.I.R.A." >> Lira.desktop
echo "Icon=$DIR/icons/xdiagnose-lira.png" >> Lira.desktop
echo "GenericName[en_US]=Classify Bacterial Lesions" >> Lira.desktop

sudo mv Lira.desktop /usr/share/applications/Lira.desktop

curl https://downloads.imagej.net/fiji/latest/fiji-linux64.zip --output $DIR/fiji.zip
unzip $DIR/fiji.zip -d $DIR/src/
rm $DIR/fiji.zip

#curl "https://github-production-release-asset-2e65be.s3.amazonaws.com/827644/8a53fdea-e78e-11e4-924c-17364713e88f?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAIWNJYAX4CSVEH53A%2F20200318%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20200318T220838Z&X-Amz-Expires=300&X-Amz-Signature=e74468f59b05575e81762c075d3eb4cd57e571e12f3154998fc3d081fe2bff0b&X-Amz-SignedHeaders=host&actor_id=0&response-content-disposition=attachment%3B%20filename%3Dopenslide-3.4.1.tar.gz&response-content-type=application%2Foctet-stream" > $DIR/openslide.tar.gz
sudo apt-get install python3-openslide
sudo apt-get install openslide-tools

curl -s https://packagecloud.io/install/repositories/github/git-lfs/script.deb.sh | sudo bash
sudo apt-get install git-lfs
git lfs install
git lfs track $DIR/classifiers/*h5
git lfs pull

mkdir $DIR/../Input\ Images
mkdir $DIR/../Output\ Stats
mkdir $DIR/data
mkdir $DIR/data/images
mkdir $DIR/data/user_progress
mkdir $DIR/data/type_one_detections_before_editing
mkdir $DIR/data/type_one_detections_after_editing
mkdir $DIR/data/prediction_grids_before_editing
mkdir $DIR/data/prediction_grids_after_editing
mkdir $DIR/data/unit_tests