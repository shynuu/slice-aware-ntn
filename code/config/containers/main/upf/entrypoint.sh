RAN_IP=A
CLASSIFIER_IP=A
ip route add $RAN_IP via $CLASSIFIER_IP
free5gc-upfd -c upfcfg.yaml