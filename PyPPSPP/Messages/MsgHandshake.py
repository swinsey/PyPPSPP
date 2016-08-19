from GlobalParams import GlobalParams as GB
from Messages.MessageTypes import MsgTypes

from struct import pack, pack_into, unpack
from array import array

class MsgHandshake(object):
    """A class representing PPSPP handshake message"""

    def __init__(self):
        self.version = GB.version
        self.min_version = GB.min_version
        self.content_identity_protection = GB.content_protection_scheme
        self.swarm = 0
        self.merkle_tree_hash_func = 2
        self.live_signature_alg = 0
        self.chunk_addressing_method = GB.chunk_addressing_method
        self.live_discard_window = 0
        self.supported_messages_len = GB.supported_messages_len
        self.supported_messages = GB.supported_messages
        self.chunk_size = GB.chunk_size

        # Used during handshake
        self.our_channel = 0
        self.their_channel = 0

        self._is_goodbye = False

    def BuildGoodbye(self):
        """Build HANDSHAKE indicating that we are leaving"""
        
        wb = bytearray()
        wb[0:] = pack('>cI', bytes([MsgTypes.HANDSHAKE]), 0)

        self._is_goodbye = True
        return wb

    def BuildBinaryMessage(self):
        """Build HANDSHAKE message. Ref [RFC7574] §7"""
        
        wb = bytearray(512)
        offset = 0

        # Packing is done in sorted way

        # [0] Version
        pack_into('cc', wb, offset, bytes([0]), bytes([self.version]))
        offset = offset + 2

		# [1] Minimum version
        pack_into('cc', wb, offset, bytes([1]), bytes([self.min_version]))
        offset = offset + 2

        # [2] Swarm identifier
        swid_len = len(self.swarm)
        pack_into('>cH', wb, offset, bytes([2]), swid_len)
        offset = offset + 1 + 2
        
        wb[offset:offset+swid_len] = self.swarm
        offset = offset + swid_len

        # [3] Content Integrity Protection Method
        pack_into('cc', wb, offset, bytes([3]), bytes([self.content_identity_protection]))
        offset = offset + 2

        # [4] Merkle Tree Hash Function
        if self.content_identity_protection == 1:
            pack_into('cc', wb, offset, bytes([4]), bytes([self.merkle_tree_hash_func]))
            offset = offset + 2

        # [5] Live signature Algorith
        if (self.content_identity_protection == 2 or self.content_identity_protection == 3):
            pack_into('cc', wb, offset, bytes([5]), bytes([self.live_signature_alg]))
            offset = offset + 2

        # [6] Chunk addressing method
        pack_into('cc', wb, offset, bytes([6]), bytes([self.chunk_addressing_method]))
        offset = offset + 2

        # [7] Live discard window
        # Not according to specs!!!
        if self.live_discard_window != 0:
            pack_into('>ci', wb, offset, 7, self.live_discard_window)
            offset = offset + 5

        # [8] Supported messages
        # Not according to specs!!!
        pack_into('ccs', wb, offset, bytes([8]), bytes([self.supported_messages_len]), bytes([255, 255]))
        offset = offset + 4

        # [9] Chunk size
        pack_into('>ci', wb, offset, bytes([9]), self.chunk_size)
        offset = offset + 5

        # [255] End option
        pack_into('c', wb, offset, bytes([255]))
        offset = offset + 1

        return wb[0:offset]

    def ParseReceivedData(self, data):
        """Parse received data until all HANDSHAKE message is parsed"""

        idx = 0
        finish_parsing = False

        while finish_parsing == False:
            next_tag = data[idx]

            if next_tag == 0:
                idx = idx + 1
                self.version = data[idx]
                idx = idx + 1
            elif next_tag == 1:
                idx = idx + 1
                self.min_version = data[idx]
                idx = idx + 1
            elif next_tag == 2:
                idx = idx + 1
                swarm_len = unpack('>H', data[idx:idx+2])[0]
                idx = idx + 2
                self.swarm = data[idx:idx+swarm_len]
                idx = idx + swarm_len
                idx = idx + 1
            elif next_tag == 3:
                idx = idx + 1
                self.content_identity_protection = data[idx]
                idx = idx + 1
            elif next_tag == 4:
                idx = idx + 1
                self.merkle_tree_hash_func = data[idx]
                idx = idx + 1
            elif next_tag == 5:
                idx = idx + 1
                self.live_signature_alg = data[idx]
                idx = idx + 1
            elif next_tag == 6:
                idx = idx + 1
                self.chunk_addressing_method = data[idx]
                idx = idx + 1
            elif next_tag == 7:
                # TODO implement
                idx = idx + 1
            elif next_tag == 8:
                idx = idx + 1
                self.supported_messages_len = data[idx]
                idx = idx + 1
                self.supported_messages = data[idx:idx+self.supported_messages_len]
                idx = idx + 1
            elif next_tag == 9:
                idx = idx + 1
                self.chunk_size = unpack('>I', data[idx:idx+4])[0]
                idx = idx + 1
            elif next_tag == 255:
                return idx + 1
            
    def __str__(self):
        if self._is_goodbye == True:
            return str("[HANDSHAKE] Goodbye!")
        else:
            return str("[HANDSHAKE] LocCh: {0}; RemCh: {1}".format(self.our_channel, self.their_channel))

    def __repr__(self):
        return self.__str__()