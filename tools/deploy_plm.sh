function __readINI() {
 INIFILE=$1; SECTION=$2; ITEM=$3
 _readIni=`awk -F '=' '/\['$SECTION'\]/{a=1}a==1&&$1~/'$ITEM'/{print $2;exit}' $INIFILE`
echo ${_readIni}
}

SECTION=PLM
ITEM=glm_port
INIFILE=config/conf.ini

SERVER_PORT=( $( __readINI $INIFILE $SECTION $ITEM) )
echo ${SERVER_PORT}
cd tools/PLM
uvicorn plm_app:app  --port ${SERVER_PORT} --host '0.0.0.0'  --reload --debug