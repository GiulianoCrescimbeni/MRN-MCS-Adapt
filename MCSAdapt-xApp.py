import src.e2ap_xapp as e2ap_xapp
from time import sleep
from ricxappframe.e2ap.asn1 import IndicationMsg

import sys
sys.path.append("oai-oran-protolib/builds/")
from ran_messages_pb2 import *
import os

ber_threshold_dl = 0
forced_mcs_dl = 0
ue_state = {}

def xappLogic():
    ber_threshold_dl = float(input("\nDL BER Threshold: "))
    forced_mcs_dl = int(input("\nForced DL MCS: "))
    print("\n")

    # instanciate xapp 
    connector = e2ap_xapp.e2apXapp()

    # get gnbs connected to RIC
    gnb_id_list = connector.get_gnb_id_list()
    print("{} gNB connected to RIC, listing:".format(len(gnb_id_list)))
    for gnb_id in gnb_id_list:
        print(gnb_id)
    print("---------")

    # subscription requests
    for gnb in gnb_id_list:
        e2sm_buffer = e2sm_report_request_buffer()
        connector.send_e2ap_sub_request(e2sm_buffer,gnb)
    
    # read loop
    sleep_time = 0.5
    while True:
        print("Sleeping {}s...".format(sleep_time))
        sleep(sleep_time)
        messgs = connector.get_queued_rx_message()
        if len(messgs) == 0:
            print("{} messages received while waiting".format(len(messgs)))
            print("____")
        else:
            print("{} messages received while waiting, printing:".format(len(messgs)))
            for msg in messgs:
                if msg["message type"] == connector.RIC_IND_RMR_ID:
                    print("RIC Indication received from gNB {}, decoding E2SM payload".format(msg["meid"]))
                    indm = IndicationMsg()
                    indm.decode(msg["payload"])
                    resp = RAN_indication_response()
                    resp.ParseFromString(indm.indication_message)
                    for entry in resp.param_map:
                        if entry.key == RAN_parameter.UE_LIST:
                            ue_list = entry.ue_list
                            os.system('clear')
                            print(f"Connected UEs: {ue_list.connected_ues}")
                            for ue in ue_list.ue_info:
                                # Printing UEs informations
                                print("______________________\n")
                                rnti = ue.rnti
                                print(f"RNTI: {rnti}")

                                if ue.HasField("ber_dl"):
                                    print(f"BER DL: {ue.ber_dl}")

                                if ue.HasField("mcs_dl"):
                                    print(f"MCS DL: {ue.mcs_dl}")

                                # Register the ue in the map
                                if rnti not in ue_state:
                                    ue_state[rnti] = {"forced": False, "original_mcs": ue.mcs_dl}

                                # Over BER threshold, forcing MCS
                                if ue.ber_dl > ber_threshold_dl and not ue_state[rnti]["forced"]:
                                    print("Forcing MCS DL...")
                                    ue_state[rnti]["original_mcs"] = ue.mcs_dl
                                    ue_state[rnti]["forced"] = True
                                    control_buffer = e2sm_control_request_buffer(rnti, forced_mcs_dl)
                                    connector.send_e2ap_control_request(control_buffer, gnb)

                                # Under BER threshold, retrieving old MCS
                                elif ue.ber_dl <= ber_threshold_dl and ue_state[rnti]["forced"]:
                                    print("Old MCS Retrieval...")
                                    ue_state[rnti]["forced"] = False
                                    control_buffer = e2sm_control_request_buffer(rnti, ue_state[rnti]["original_mcs"])
                                    connector.send_e2ap_control_request(control_buffer, gnb)

                                print("______________________")
                else:
                    print("Unrecognized E2AP message received from gNB {}".format(msg["meid"]))

def e2sm_report_request_buffer():
    master_mess = RAN_message()
    master_mess.msg_type = RAN_message_type.INDICATION_REQUEST
    inner_mess = RAN_indication_request()
    inner_mess.target_params.extend([RAN_parameter.GNB_ID, RAN_parameter.UE_LIST])
    master_mess.ran_indication_request.CopyFrom(inner_mess)
    buf = master_mess.SerializeToString()
    return buf

def e2sm_control_request_buffer(rnti, mcs_dl):
    master_mess = RAN_message()
    master_mess.msg_type = RAN_message_type.CONTROL
    inner_mess = RAN_control_request()
    
    # ue list map entry
    ue_list_control_element = RAN_param_map_entry()
    ue_list_control_element.key = RAN_parameter.UE_LIST
    
    # ue list message 
    ue_list_message = ue_list_m()
    ue_list_message.connected_ues = 1 # this will not be processed by the gnb, it can be anything

    # ue info message
    ue_info_message = ue_info_m()
    ue_info_message.rnti = rnti
    ue_info_message.mcs_dl = mcs_dl

    # put info message into repeated field of ue list message
    ue_list_message.ue_info.extend([ue_info_message])

    # put ue_list_message into the value of the control map entry
    ue_list_control_element.ue_list.CopyFrom(ue_list_message)

    # finalize and send
    inner_mess.target_param_map.extend([ue_list_control_element])
    master_mess.ran_control_request.CopyFrom(inner_mess)
    buf = master_mess.SerializeToString()
    return buf

if __name__ == "__main__":
    xappLogic()