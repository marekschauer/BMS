#!/usr/bin/env python3.6

# Description:	Simple DVBT transport stream analyser
# 				Project for BMS class at VUT FIT Brno
# Class:		BMS
# Author: 		Marek Schauer (xschau00)
# Year: 		2019

import argparse
import sys
import constants

# Byte AND
def byte_and(ba1, ba2):
    size = len(ba1) if len(ba1) < len(ba2) else len(ba2)
    toBeReturned = bytearray(size)
    for i in range(size):
    	toBeReturned[i] = ba1[i] & ba2[i]
    return toBeReturned

class TransportStream():
	"""docstring for TransportStream"""
	def __init__(self):
		self.network_name 				= None
		self.networkID 					= None
		self.bandwidth 					= None
		self.constellation 				= None
		self.code_rate 					= None
		self.guard_interval				= None

		# Dictionary that associates `program_number`
		# to PID of PMT packet
		self.program_map_PIDs			= {}
		
		# Container for informations about each program
		# Associates `program_number` to `ProgramInformations` object
		self.programs_info 				= {}

		# Count of all packets in the stream
		self.packets_count 				= 0
		
		# elementaryPID => count
		self.elementary_PIDs_Counters	= {}
		
		# PID of PMTs => count
		self.PMT_PIDs_Counters			= {}
		
		# Associates elementary stream PIDs
		# to program numbers.
		# `elementaryPID` => `program_number`
		self.elementary_to_program 		= {}

		# Counter for each PID in transport stream
		# `PID` => `counter`
		self.packets_conuters			= {}
		

	def calculateProgramBitrates(self):
		bitrateVars = [self.bandwidth, self.constellation, self.code_rate, self.guard_interval]
		if None in bitrateVars:
			print("Unable to calculate bitrate", file=sys.stderr)
			sys.exit()

		program_packets_count = 0
		for program_number_1, program_info in self.programs_info.items():

			qpskVals = {"QPSK": 1/4, "16-QAM" : 1/2, "64-QAM" : 3/4}
			codeRateVals = {"1/2": 1/2, "2/3": 2/3, "3/4": 3/4, "5/6": 5/6, "7/8": 7/8}
			guardIntervalVals = {"1/32": 32/33, "1/16": 16/17, "1/8": 8/9, "1/4": 4/5}
			
			tmp = 54000000*(constants.PACKET_LENGTH/204)
			tmp = tmp * (self.bandwidth/8)
			tmp = tmp * qpskVals[self.constellation]
			tmp = tmp * codeRateVals[self.code_rate]
			tmp = tmp * guardIntervalVals[self.guard_interval]

			# bitrate_programu = pocet_paketu_pro_program/celkovy_pocet_paketu*bitrate_streamu
			program_packets_count = 0
			for pid, count in self.packets_conuters.items():
				if (pid in program_info.ES_PIDs) or (pid == program_info.pmt_PID):
					program_packets_count += count
			
			program_bitrate = program_packets_count / self.packets_count * tmp

			program_info.programBitrate = program_bitrate
	
	def printAnalysis(self, nameFile):
		transportStream.calculateProgramBitrates()

		f = open(nameFile, "w")
		f.write("Network name: " + str(transportStream.network_name) + "\n")
		f.write("Network ID: " + str(transportStream.networkID) + "\n")
		f.write("Bandwidth: " + str(transportStream.bandwidth) + " MHz" + "\n")
		f.write("Constellation: " + str(transportStream.constellation) + "\n")
		f.write("Guard interval: " + str(transportStream.guard_interval) + "\n")
		f.write("Code rate: " + str(transportStream.code_rate) + "\n")
		f.write("" + "\n")
		for key, program in transportStream.programs_info.items():
			f.write(str(program) + "\n")
		
		f.close()


class ProgramInformations():
	"""docstring for ProgramInformations"""
	def __init__(self, pid):
		self.pid 				= '0x{0:0{1}x}'.format(pid,4)
		self.service_provider 	= None
		self.service_name 		= None
		self.bitrate 			= None
		self.programBitrate 	= None
		self.pmt_PID 			= pid
		self.ES_PIDs			= []

	def __repr__(self):
		return self.pid + "-" + str(self.service_provider) + "-" + str(self.service_name) + ": " + str('{:0.2f}'.format(self.programBitrate/1000000)) + " Mbps"
		


class Packet:
	"""docstring for Packet"""
	def __init__(self, packetData, transportStream):
		self.packetData = packetData

		# HEADER, 4B
		self.header = packetData[0:4]
		
		# PUSI, 10th bit
		self.pusi = 0
		if byte_and(self.header[1:2], bytearray(b'\x40')) == b'\x40':
			self.pusi = 1
		
		self.body = packetData[4:]
		
		self.pointer_field = int.from_bytes(packetData[4:5], 'big')
		if self.pusi:
			self.pointer_field = packetData[4:5]
			self.body = packetData[5:]

		pidByteArr = byte_and(self.header, bytearray(b'\x00\x1F\xFF\x00'))[:-1]
		self.pid = int.from_bytes(pidByteArr, 'big')
		self.table_id = self.body[0]
		
		self.continuity_counter = int.from_bytes(byte_and(self.header[-1:], b'\x0F'), 'big')
		self.transportStream = transportStream
	def __repr__(self):
		return "================\n\nheader: " + str(self.header) + "(" + str(len(self.header)) + "B)\n" + "pusi: " + str(self.pusi) + "\npointer_field: " + str(self.pointer_field) + "\n" + "body: " + str(self.body) + "(" + str(len(self.body)) + "B)\n" + "pid: " + str(self.pid) + "\n" + "table_id: " + str(self.table_id) + "\n" + "continuity_counter: " + str(self.continuity_counter) + "\n"
		

class PATPacket(Packet):
	"""docstring for PATPacket"""
	def __init__(self, packetData, transportStream):
		super(PATPacket, self).__init__(packetData, transportStream)
		self.transport_stream_id =  int.from_bytes(self.body[3:5], 'big')
		self.section_length = int.from_bytes(byte_and(self.body[1:3], b'\x0F\xFF'), 'big')
		self.section = self.body[3:(3+self.section_length)]
		self.parseSection(self.section)

	def parseSection(self, section):
		self.section_loop_body_length = len(section) - 9
		self.section_loop_body = section[5:(5+self.section_loop_body_length)]
		self.parseSectionLoop(self.section_loop_body)

	def parseSectionLoop(self, section_loop):
		self.program_map_PIDs = {}
		current_index = 0

		while True:
			program_number = int.from_bytes(section_loop[current_index:(current_index+2)], 'big')
			if program_number != 0:
				program_map_PID = int.from_bytes(byte_and(section_loop[(current_index+2):((current_index+2)+2)], b'\x1F\xFF'), 'big')
				self.program_map_PIDs[program_number] = program_map_PID
				if program_number not in self.transportStream.programs_info.keys():
					self.transportStream.programs_info[program_number] = ProgramInformations(program_map_PID)
				
				# Ak v self.transportStream.PMT_PIDs_Counters neexistuje index s hodnotou program_map_PID, 
				# tak taky prvok vytvorime a dame hodnotu counteru rovnu 0
				if program_map_PID not in self.transportStream.PMT_PIDs_Counters.keys():
					self.transportStream.PMT_PIDs_Counters[program_map_PID] = 0

			current_index = ((current_index+2)+2)

			if current_index >= len(section_loop):
				break

		self.transportStream.program_map_PIDs = self.program_map_PIDs




class PMTPacket(Packet):
	"""docstring for PMTPacket"""
	def __init__(self, packetData, transportStream):
		super(PMTPacket, self).__init__(packetData, transportStream)
		self.section_length = int.from_bytes(byte_and(self.body[1:3], b'\x0F\xFF'), 'big')
		self.section = self.body[3:(3+self.section_length)]
		self.parseSection(self.section)

	def parseSection(self, section):
		self.program_number = int.from_bytes(section[0:2], 'big')
		self.program_info_length = int.from_bytes(byte_and(section[7:9], b'\x0F\xFF'), 'big')
		self.es_loop_length = len(section) - self.program_info_length - 9
		self.es_loop_body = section[(9 + self.program_info_length):((9 + self.program_info_length) + self.es_loop_length)]

		self.transportStream.PMT_PIDs_Counters[self.pid] += 1

		self.parseESLoopBody(self.es_loop_body)

	def parseESLoopBody(self, es_loop_body):
		current_index = 0
		while True:
			elementaryPID = int.from_bytes(byte_and(es_loop_body[(current_index + 1):(current_index + 3)], b'\x1F\xFF'), 'big')
			es_info_length = int.from_bytes(byte_and(es_loop_body[(current_index + 3):(current_index + 5)], b'\x0F\xFF'), 'big')
			current_index = current_index + 5 + es_info_length
			
			if elementaryPID not in self.transportStream.elementary_PIDs_Counters.keys():
				self.transportStream.elementary_PIDs_Counters[elementaryPID] = 0

			self.transportStream.elementary_to_program[elementaryPID] = self.program_number

			if elementaryPID not in self.transportStream.programs_info[self.program_number].ES_PIDs:
				self.transportStream.programs_info[self.program_number].ES_PIDs.append(elementaryPID)

			if current_index >= len(es_loop_body):
				break
			
		



class SDTPacket(Packet):
	"""docstring for SDTPacket"""
	def __init__(self, packetData, transportStream):
		super(SDTPacket, self).__init__(packetData, transportStream)
		if self.pusi == 1:
			self.section_length = int.from_bytes(byte_and(self.body[1:3], b'\x0F\xFF'), 'big')
			self.section = self.body[3:(3+self.section_length)]
			# self.parseSection(self.section)

	def parseSection(self, section):
		self.section_number = section[3:4]
		self.last_section_number = section[4:5]
		self.section_loop_body_length = len(section) - 12
		self.section_loop_body = section[8:(8+self.section_loop_body_length)]
		self.parseSectionLoop(self.section_loop_body)

	def parseSectionLoop(self, section_loop_body):
		current_index = 0
		while True:
			self.service_id = int.from_bytes(section_loop_body[current_index:(current_index+2)], 'big')
			descriptors_loop_length = int.from_bytes(byte_and(section_loop_body[(current_index+3):(current_index+5)], b'\x0F\xFF'), 'big')
			descriptors_body = section_loop_body[(current_index+5):(current_index+5+descriptors_loop_length)]
			self.parseDescriptors(descriptors_body)
			current_index = current_index+5+descriptors_loop_length

			# tag == \x48 = 72(dec)
			if current_index >= len(section_loop_body):
				break
	
	def parseDescriptors(self, section_loop_body):
		current_index = 0
		while True:
			descriptor_tag = int.from_bytes(section_loop_body[current_index:(current_index+1)], 'big')
			if descriptor_tag == 72:
				service_provider_name_length = int.from_bytes(section_loop_body[(current_index+3):(current_index+4)], 'big')
				service_provider_name = section_loop_body[(current_index+4):(current_index+4+service_provider_name_length)]
				service_name_length = int.from_bytes(section_loop_body[(current_index+4+service_provider_name_length):(current_index+4+service_provider_name_length+1)], 'big')
				service_name = section_loop_body[(current_index+4+service_provider_name_length+1):(current_index+4+service_provider_name_length+1+service_name_length)]
				if self.service_id in self.transportStream.programs_info.keys():
					if isinstance(self.transportStream.programs_info[self.service_id], ProgramInformations):
						self.transportStream.programs_info[self.service_id].service_provider = service_provider_name.decode("utf-8")
						self.transportStream.programs_info[self.service_id].service_name = service_name.decode("utf-8")
				current_index = (current_index+5+service_provider_name_length+1+service_name_length)

			if current_index >= len(section_loop_body):
				break

	def concatenateBody(self, anotherSTDPacket):
		self.section = (self.section + anotherSTDPacket.body)[0:self.section_length]
		
		if len(self.section) >= self.section_length:
			self.parseSection(self.section)
			pass


class ElementaryPacket(Packet):
	"""docstring for ElementaryPacket"""
	def __init__(self, packetData, transportStream):
		super(ElementaryPacket, self).__init__(packetData, transportStream)
		self.transportStream.elementary_PIDs_Counters[self.pid] += 1


class NITPacket(Packet):
	"""docstring for NITPacket"""
	def __init__(self, packetData, transportStream):
		super(NITPacket, self).__init__(packetData, transportStream)
		self.networkID = int.from_bytes(self.body[3:5], 'big')
		self.transportStream.networkID = self.networkID
		self.network_descriptors_length = int.from_bytes(byte_and(self.body[8:10], b'\x0F\xFF'), 'big')
		self.network_descriptor_first_tag = self.body[10:11]
		self.network_descriptors = self.body[10:(10+self.network_descriptors_length)]
		self.network_name = None
		self.parseDescriptors(self.network_descriptors)
		self.ts_loop_length = int.from_bytes(byte_and(self.body[(10+self.network_descriptors_length):(10+self.network_descriptors_length+2)], b'\x0F\xFF'), 'big')
		self.ts_loop = self.body[(10+self.network_descriptors_length+2):(10+self.network_descriptors_length+2+self.ts_loop_length)]
		self.parseTSLoop(self.ts_loop)

	def parseDescriptors(self, network_descriptors):
		current_index = 0
		while True:
			current_descriptor_tag = network_descriptors[current_index]
			current_descriptor_length = network_descriptors[current_index + 1]
			current_descriptor_body = network_descriptors[(current_index+2):((current_index+2)+current_descriptor_length)]
			current_index = (current_index+2)+current_descriptor_length

			if current_descriptor_tag == 64:
				self.network_name = current_descriptor_body
				self.transportStream.network_name = self.network_name.decode("utf-8")

			if current_index >= len(network_descriptors):
				break
	
	def parseTSLoop(self, ts_loop):
		current_index = 0
		while True:
			current_transport_stream_id = int.from_bytes(ts_loop[current_index:current_index+2], 'big')
			original_network_id = int.from_bytes(ts_loop[current_index+2:current_index+2+2], 'big')
			transport_descriptors_length = int.from_bytes(byte_and(ts_loop[current_index+2+2:current_index+2+2+2], b'\x0F\xFF'), 'big')
			transport_descriptors = ts_loop[(current_index+2+2+2):(current_index+2+2+2+transport_descriptors_length)]
			self.parseTransportDescriptors(transport_descriptors)
			
			current_index = current_index+2+2+2+transport_descriptors_length
			if current_index >= len(ts_loop):
				break

	def parseTransportDescriptors(self, transport_descriptors):
		current_index = 0
		while True:
			current_descriptor_tag = transport_descriptors[current_index]
			current_descriptor_length = transport_descriptors[current_index + 1]
			current_descriptor_body = transport_descriptors[(current_index+2):((current_index+2)+current_descriptor_length)]
			current_index = (current_index+2)+current_descriptor_length

			if current_descriptor_tag == 90:
				bandwidth = int.from_bytes(byte_and(current_descriptor_body[4:5], b'\xE0'), 'big') / 32
				if bandwidth == 0:
					self.transportStream.bandwidth = 8
				elif bandwidth == 1:
					self.transportStream.bandwidth = 7
				elif bandwidth == 2:
					self.transportStream.bandwidth = 6
				elif bandwidth == 3:
					self.transportStream.bandwidth = 5

				constellation = int.from_bytes(byte_and(current_descriptor_body[5:6], b'\xC0'), 'big') / 64
				if constellation == 0:
					self.transportStream.constellation = "QPSK"
				elif constellation == 1:
					self.transportStream.constellation = "16-QAM"
				elif constellation == 2:
					self.transportStream.constellation = "64-QAM"


				code_rate = int.from_bytes(byte_and(current_descriptor_body[5:6], b'\x07'), 'big')
				if code_rate == 0:
					self.transportStream.code_rate = "1/2"
				elif code_rate == 1:
					self.transportStream.code_rate = "2/3"
				elif code_rate == 2:
					self.transportStream.code_rate = "3/4"
				elif code_rate == 3:
					self.transportStream.code_rate = "5/6"
				elif code_rate == 4:
					self.transportStream.code_rate = "7/8"

				guard_interval = int.from_bytes(byte_and(current_descriptor_body[6:7], b'\x18'), 'big') / 8
				if guard_interval == 0:
					self.transportStream.guard_interval = "1/32"
				elif guard_interval == 1:
					self.transportStream.guard_interval = "1/16"
				elif guard_interval == 2:
					self.transportStream.guard_interval = "1/8"
				elif guard_interval == 3:
					self.transportStream.guard_interval = "1/4"



			if current_index >= len(transport_descriptors):
				break


# ###############################################################
# ###############################################################
# ###############################################################
# ################# START OF PROGRAM EXECUTION ##################
# ###############################################################
# ###############################################################
# ###############################################################
parser = argparse.ArgumentParser()
parser.add_argument("inputFileName", help="The name of input file")
args = parser.parse_args()

packetHeader 		= bytearray(4)
cnt 				= 0
cntZeroPID 			= 0
pusiCNT				= 0
packets 			= []
patPackets 			= []
nitPackets 			= []
tableIds			= set()
pointer_fields		= set()
network_descriptor_first_tags 	= set()
network_descriptors_lengths 	= set()
tmpDontUseMe		= []
transportStream 	= TransportStream()

with open(args.inputFileName, 'rb') as binary_file:
	while True:
		cnt = cnt + 1
		packet = binary_file.read(188)
		if not packet:
			break
		packetObj = Packet(packet, transportStream)

		# Counting each packet even if we don't exactly know, what it is
		if packetObj.pid not in transportStream.packets_conuters.keys():
			transportStream.packets_conuters[packetObj.pid] = 0
		else:
			transportStream.packets_conuters[packetObj.pid] += 1			

		packets.append(packet)

		packetHeader = packetObj.header
		packetBody = packetObj.body

		if packetObj.pusi:
			pusiCNT += 1;
			pointer_fields.add(packetObj.pointer_field)


		packetPID = packetObj.pid
		if packetPID == 0:
			patPacket = PATPacket(packet, transportStream)
		elif packetPID == 16:
			nitPacket = NITPacket(packet, transportStream)
		elif packetPID == 17:
			actualSdtPacket = SDTPacket(packet, transportStream)
			if actualSdtPacket.pusi == 1:
				sdtPacket = SDTPacket(packet, transportStream)
			else:
				sdtPacket.concatenateBody(actualSdtPacket)
		elif packetPID in transportStream.program_map_PIDs.values():
			pmtPacket = PMTPacket(packet, transportStream)
		elif packetPID in transportStream.elementary_PIDs_Counters.keys():
			elementaryPacket = ElementaryPacket(packet, transportStream)

		transportStream.packets_count += 1

outputFileName = args.inputFileName[0:(len(args.inputFileName)-3)] + ".txt"
transportStream.printAnalysis(outputFileName)

