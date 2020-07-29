#!/usr/bin/python

#/* ############################################################ */
#/* //////////////////////////////////////////////////////////// */
#/* */
#/* //////////////////////////////////////////////////////////// */
#/* ############################################################ */
from . import wam_log as log
from . import wam_debug as DEBUG
from . import wam_util as util
from . import wam_error as error

from . import protobuf as message

import json
import base64

#/* ############################################################ */
#/* //////////////////////////////////////////////////////////// */
#/* */
#/* //////////////////////////////////////////////////////////// */
#/* ############################################################ */

_pb_tx_type_dicts = {
	"p2pkh" : message.transaction_type_t.p2pkh,
	"p2pk" : message.transaction_type_t.p2pk,
	"p2sh" : message.transaction_type_t.p2sh,
	"p2wpkh" : message.transaction_type_t.p2wpkh,
	"p2wsh" : message.transaction_type_t.p2wsh,
	"multisig" : message.transaction_type_t.multisig,
	"change" : message.transaction_type_t.change
}

_pb_json_map_dicts = {
	"transaction_type" : _pb_tx_type_dicts,
}

def convert_dics(dics):
	converted_dics = {}
	for (key, value) in dics.items():
		converted_dics[value] = key
	return converted_dics

def pb_get(key, json_value):
	dicts = _pb_json_map_dicts[key]
	return dicts[json_value]

def json_get(key, pb_value):
	dicts = _pb_json_map_dicts[key]
	new_dicts = convert_dics(dicts)
	return new_dicts[pb_value]

#/* ############################################################ */
#/* //////////////////////////////////////////////////////////// */
#/* */
#/* //////////////////////////////////////////////////////////// */
#/* ############################################################ */

# related with bitcoin.proto
def get_transaction_blk_size():
	return 8000

def get_message_sign_init_blk_size():
	return 7000

def get_message_update_blk_size():
	return 8000

#/* ############################################################ */
#/* //////////////////////////////////////////////////////////// */
#/* */
#/* //////////////////////////////////////////////////////////// */
#/* ############################################################ */

def get_input_max_count():
	return 50

def get_output_max_count():
	return 10

def pb_get_parameter_transaction_wp_begin(json_parameter):

	if len(json_parameter["input"]) > get_input_max_count():
		error.raiseWam("max input num is " + str(get_input_max_count()))
	elif len(json_parameter["output"]) > get_output_max_count():
		error.raiseWam("max output num is " + str(get_output_max_count()))

	##
	#

	#log.dump_json("param", json_parameter)
	pb_parameter = message.transaction_begin_req_zcash_parameter_t()

	pb_parameter.version = json_parameter["version"]
	pb_parameter.tx_blk_size = get_transaction_blk_size()

	##
	#

	for param_input in json_parameter["input"]:
		pb_input = message.transaction_input_t()
		pb_input.prev_tx_size = util.len_hexstring(param_input["prev_tx"])
		pb_input.utxo_idx = param_input["utxo_idx"]
		pb_input.type = pb_get("transaction_type", param_input["type"])
		pb_input.key_path = param_input["key"]
		if "sequence" in param_input:
  			pb_input.sequence=param_input["sequence"]
		pb_parameter.input.append(pb_input)
				
	for param_output in json_parameter["output"]:
		# pb_output = pb_parameter.output.add()
		pb_output = message.transaction_output_t()
		pb_output.type = pb_get("transaction_type", param_output["type"])
		pb_output.value = param_output["value"]
		pb_output.to_address.extend(param_output["to"])
		pb_parameter.output.append(pb_output)

	pb_parameter.locktime = json_parameter["locktime"]

	if "option" in json_parameter:
		opt_data = json_parameter["option"]
		opt_data = util.string2hexbin(opt_data)
		pb_parameter.sign_param.param_data = opt_data

	return util.pb_serializeToString(pb_parameter)

def pb_get_parameter_transaction_begin(json_parameter):

	if len(json_parameter["input"]) > get_input_max_count():
		error.raiseWam("max input num is " + str(get_input_max_count()))
	elif len(json_parameter["output"]) > get_output_max_count():
		error.raiseWam("max output num is " + str(get_output_max_count()))

	##
	#

	#log.dump_json("param", json_parameter)
	pb_parameter = message.transaction_begin_req_parameter_t()
	pb_parameter.version = json_parameter["version"]
	pb_parameter.tx_blk_size = get_transaction_blk_size()

	##
	#

	for param_input in json_parameter["input"]:
		pb_input = message.transaction_input_t()
		pb_input.prev_tx_size = util.len_hexstring(param_input["prev_tx"])
		pb_input.utxo_idx = param_input["utxo_idx"]
		pb_input.type = pb_get("transaction_type", param_input["type"])
		pb_input.key_path = param_input["key"]
		if "sequence" in param_input:
  			pb_input.sequence=param_input["sequence"]
		pb_parameter.input.append(pb_input)

	for param_output in json_parameter["output"]:
		pb_output = message.transaction_output_t()
		pb_output.type = pb_get("transaction_type", param_output["type"])
		pb_output.value = param_output["value"]
		pb_output.to_address.extend(param_output["to"])
		pb_parameter.output.append(pb_output)

	pb_parameter.locktime = json_parameter["locktime"]

	return util.pb_serializeToString(pb_parameter)

def pb_get_parameter_transaction_update_prevtx(input_idx, prev_tx_blk_idx, prev_tx_blk):
	pb_parameter = message.transaction_update_prevtx_req_parameter_t()
	pb_parameter.input_idx = input_idx
	pb_parameter.prev_tx_blk_idx = prev_tx_blk_idx
	pb_parameter.prev_tx_blk = prev_tx_blk
	return util.pb_serializeToString(pb_parameter)

def encode_transaction(request_to, version, json_parameter):
	pb_request_list = []

	##
	# transaction_begin

	pb_request = util.pb_makeTransactionReq()
	pb_request.header.version = version
	pb_request.header.request_to = request_to

	if request_to == message.cointype_t.zcash or request_to == message.cointype_t.zcash_testnet:
		pb_request.body.command.value = message.bitcoin_t.btc_transaction_begin_zc
		pb_request.body.parameter = pb_get_parameter_transaction_wp_begin(json_parameter)
	else:
		pb_request.body.command.value = message.bitcoin_t.btc_transaction_begin
		pb_request.body.parameter = pb_get_parameter_transaction_begin(json_parameter)



	pb_request_list.append(pb_request)

	##
	# transaction_update_script

	input_idx = 0
	for param_input in json_parameter["input"]:
		if 'script' in param_input:
			script = param_input["script"]
			script = util.string2hexbin(script)
			DEBUG.NOT_IMPLEMENTED()

	##
	# transaction_update_prevtx

	input_idx = 0
	TRANSACTION_BLK_SIZE = get_transaction_blk_size()
	for param_input in json_parameter["input"]:
		prev_tx = param_input["prev_tx"]
		prev_tx = util.string2hexbin(prev_tx)
		prev_tx_blk_idx = 0
		while len(prev_tx) > 0:
			prev_tx_blk = prev_tx[:TRANSACTION_BLK_SIZE]
			log.d("prev_tx : "+str(prev_tx))
			log.d("len(prev_tx_blk) : "+str(len(prev_tx_blk)))

			pb_request = util.pb_makeTransactionReq()
			pb_request.header.version = version
			pb_request.header.request_to = request_to

			pb_request.body.command.value = message.bitcoin_t.btc_transaction_update_prevtx
			pb_request.body.parameter = pb_get_parameter_transaction_update_prevtx(
																input_idx,
																prev_tx_blk_idx,
																prev_tx_blk
																)
			pb_request_list.append(pb_request)
			prev_tx = prev_tx[TRANSACTION_BLK_SIZE:]
			prev_tx_blk_idx += 1
			log.d("prev_tx : "+str(prev_tx))
			log.d("len(prev_tx) : "+str(len(prev_tx)))

		input_idx += 1

	##
	# transaction_finish

	pb_request = util.pb_makeTransactionReq()
	pb_request.header.version = version
	pb_request.header.request_to = request_to

	pb_request.body.command.value = message.bitcoin_t.btc_transaction_finish

	pb_request_list.append(pb_request)

	##
	# transaction_retrieve

	pb_request = util.pb_makeTransactionReq()
	pb_request.header.version = version
	pb_request.header.request_to = request_to

	pb_request.body.command.value = message.bitcoin_t.btc_transaction_retrieve

	pb_request_list.append(pb_request)

	return pb_request_list

def get_keypath_max_size():
	return 51

def pb_get_parameter_get_address(json_parameter):
	if len(json_parameter["path"]) >= get_keypath_max_size():
		error.raiseWam("key path too long. max = " + str(get_keypath_max_size()))

	pb_parameter = message.get_address_req_parameter_t()

	pb_parameter.key_path = json_parameter["path"]

	return util.pb_serializeToString(pb_parameter)


def encode_get_address(request_to, version, json_parameter):
	pb_request_list = []

	pb_request = util.pb_makeTransactionReq()
	pb_request.header.version = version
	pb_request.header.request_to = request_to

	pb_request.body.command.value = message.bitcoin_t.btc_get_address
	pb_request.body.parameter = pb_get_parameter_get_address(json_parameter)

	pb_request_list.append(pb_request)

	return pb_request_list

def pb_get_parameter_msg_sign(json_parameter,init_msg_blk):
	
	pb_parameter = message.txreq_message_sign_parameter_t()

	pb_parameter.key_path = json_parameter["path"]
	pb_parameter.total_msg_len = 0
	if "message" in json_parameter:
		if not json_parameter["message"][:2]=="0x":
			pb_parameter.total_msg_len = len(json_parameter["message"])
		else:
			pb_parameter.total_msg_len = util.len_hexstring(json_parameter["message"])
	pb_parameter.message_blk = init_msg_blk
	
	return util.pb_serializeToString(pb_parameter)

def pb_get_parameter_message_update(update_blk_idx, update_blk):
	pb_parameter = message.txreq_message_sign_update_t()
	pb_parameter.message_blk_idx = update_blk_idx
	pb_parameter.message_blk = update_blk
	return util.pb_serializeToString(pb_parameter)


def encode_msg_sign(request_to, version, json_parameter):
	pb_request_list = []
	
	TRANSACTION_MESSAGE_BLK_SIZE = get_message_sign_init_blk_size()

	if "message" in json_parameter:
		msg = json_parameter["message"]		
		if not msg[:2]== "0x":
			msg = util.string2hex(msg)			
		log.d("msg : "+ msg)
		data = util.string2hexbin(msg)
		

	init_msg_blk = data[:TRANSACTION_MESSAGE_BLK_SIZE]
	data = data[TRANSACTION_MESSAGE_BLK_SIZE:]
	
	# msg_sign_init
	pb_request = util.pb_makeTransactionReq()
	pb_request.header.version = version
	pb_request.header.request_to = request_to	
	pb_request.body.command.value = message.bitcoin_t.btc_message_sign
	pb_request.body.parameter = pb_get_parameter_msg_sign(json_parameter, init_msg_blk)

	pb_request_list.append(pb_request)
	#update_message
	MESSAGE_UPDATE_BLK_SIZE = get_message_update_blk_size()
	update_blk_idx = 0

	while len(data) > 0:
		update_blk = data[:MESSAGE_UPDATE_BLK_SIZE]
	
		pb_request = util.pb_makeTransactionReq()
		pb_request.header.version = version
		pb_request.header.request_to = request_to

		pb_request.body.command.value = message.bitcoin_t.btc_message_update
		pb_request.body.parameter = pb_get_parameter_message_update(
															update_blk_idx,
															update_blk
															)
		pb_request_list.append(pb_request)
		data = data[MESSAGE_UPDATE_BLK_SIZE:]
		update_blk_idx += 1

	#msg_sign_finish
	pb_request = util.pb_makeTransactionReq()
	pb_request.header.version = version
	pb_request.header.request_to = request_to

	pb_request.body.command.value = message.bitcoin_t.btc_message_sign_finish

	pb_request_list.append(pb_request)

	return pb_request_list

def encode(request_to, version, json_body):
	command = json_body["command"]
	if command == "transaction":
		pb_request_list = encode_transaction(request_to, version, json_body["parameter"])
	elif command == "get_address":
		pb_request_list = encode_get_address(request_to, version, json_body["parameter"])
	elif command == "msg_sign":
		pb_request_list = encode_msg_sign(request_to, version, json_body["parameter"])
	else:
		DEBUG.NOT_SUPPORTED()

	return pb_request_list

#/* ############################################################ */
#/* //////////////////////////////////////////////////////////// */
#/* */
#/* //////////////////////////////////////////////////////////// */
#/* ############################################################ */

def decode_transaction(command, pb_response_list):
	next_blk_idx = 0
	signed_str = ""
	for pb_response in pb_response_list:
		if pb_response.body.error is not None:
			DEBUG.NOT_REACHED()	# Error already Checked

		if pb_response.body.command.value == message.bitcoin_t.btc_transaction_retrieve:
			pb_parameter = util.pb_serializeFromString(pb_response.body.parameter, message.transaction_retrieve_res_parameter_t)
			# pb_parameter.ParseFromString(pb_response.body.parameter)
			if next_blk_idx != pb_parameter.tx_blk_idx:
				DEBUG.NOT_IMPLEMENTED()
			next_blk_idx += 1
			signed_str += util.bin2hexstring(pb_parameter.tx_blk)
			log.d("signed_str = " + signed_str)

	# //

	#signed_str += ""

	json_parameter = {
		"signed" : signed_str
	}

	json_body = {
		"command" : command,
		"parameter" : json_parameter
	}

	return json_body

def decode_get_address(command, pb_response_list):
	if len(pb_response_list) != 1:
		DEBUG.NOT_REACHED()

	for pb_response in pb_response_list:
		if pb_response.body.error is not None:
			DEBUG.NOT_REACHED()	# Error already Checked

		if pb_response.body.command.value != message.bitcoin_t.btc_get_address:
			DEBUG.NOT_REACHED()

		# pb_parameter = message.get_address_res_parameter_t()
		# pb_parameter.ParseFromString(pb_response.body.parameter)
		pb_parameter = util.pb_serializeFromString(pb_response.body.parameter, message.get_address_res_parameter_t)
		this_param = pb_parameter

		json_address = this_param.address


	json_parameter = {
		"address" : json_address
	}

	json_body = {
		"command" : command,
		"parameter" : json_parameter
	}

	return json_body

def decode_msg_sign(command, pb_response_list):
	for pb_response in pb_response_list:
		if pb_response.body.error is not None:
			DEBUG.NOT_REACHED()	# Error already Checked

		if pb_response.body.command.value == message.bitcoin_t.btc_message_sign_finish:
			pb_parameter = util.pb_serializeFromString(pb_response.body.parameter, message.txres_message_sign_t)
			this_param = pb_parameter

			# msg_signed = "0x" + util.bin2hexstring(pb_parameter.msg_signed)
			msg_signed = base64.b64encode(pb_parameter.msg_signed).decode("utf-8")
			json_address = this_param.address

	# //
	
	json_parameter = {
		"address" : json_address,
		"msg_signed" : msg_signed,
	}

	json_body = {
		"command" : command,
		"parameter" : json_parameter
	}

	return json_body

def decode(command, pb_response_list):
	if command == "transaction":
		json_body = decode_transaction(command, pb_response_list)
	elif command == "get_address":
		json_body = decode_get_address(command, pb_response_list)
	elif command == "msg_sign":
		json_body = decode_msg_sign(command, pb_response_list)
	else:
		DEBUG.NOT_IMPLEMENTED()

	return json_body

#/* ############################################################ */
#/* //////////////////////////////////////////////////////////// */
#/* */
#/* //////////////////////////////////////////////////////////// */
#/* ############################################################ */
